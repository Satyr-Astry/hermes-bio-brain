"""
仿生大脑 · Hermes 工具注册 (v2)
================================
register_tools(ctx) —— Hermes 插件加载器调用的入口。

v2 升级：接的是**新大脑**（Conductor + 张量化 + 记忆库 + LLM 语言区），
        不再是旧的 64 神经元 Python 循环版。

工具（7 个）：
  brain_ask       ★对话（大脑记忆 + LLM 表达，最常用）
  brain_teach     教一条知识
  brain_distill   ★向 LLM 学习一个主题（自主蒸馏）
  brain_recall    检索记忆（看它知道什么）
  brain_think     思考流（不输出语言，只看激活）
  brain_sleep     睡眠巩固
  brain_state     大脑状态

铁律：
  · 大脑独立运行（独立进程/状态文件）
  · 不触碰 Hermes 主会话 model（防卡死网关）
  · 懒加载 + 单例（避免重复构建）
"""
from __future__ import annotations

import json
import logging
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger("hermes.plugin.bio-brain")

_HERE = Path(__file__).resolve().parent
# 大脑代码位置解析顺序：
#   1. 环境变量 BIOBRAIN_PATH（最优先，推荐）
#   2. 插件目录内的 brain/ 子目录（自带大脑时）
#   3. Hermes 配置项 plugins.bio-brain.brain_path（若存在）
_CANDIDATES_ENV = ("BIOBRAIN_PATH", "HERMES_BIOBRAIN_PATH")


def _candidate_paths() -> list:
    """按优先级返回候选大脑目录（惰性计算，便于配置热改）"""
    import os
    out = []
    for var in _CANDIDATES_ENV:
        val = (os.environ.get(var) or "").strip()
        if val:
            out.append(Path(val))
    out.append(_HERE / "brain")
    return out


def _config_path() -> Optional[Path]:
    """从 Hermes 配置读 brain_path（plugins.bio-brain.brain_path）"""
    try:
        from hermes_constants import get_hermes_home
        home = get_hermes_home()
    except Exception:
        import os
        home = Path(os.environ.get("HERMES_HOME", "") or Path.home() / ".hermes")
    cfg = Path(home) / "config.yaml"
    if not cfg.is_file():
        return None
    try:
        import yaml
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        entry = ((data.get("plugins") or {}).get("bio-brain") or {})
        val = (entry.get("brain_path") or "").strip()
        return Path(val) if val else None
    except Exception:
        return None


# ---------- 单例 ----------
_lock = threading.Lock()
_brain = None
_brain_error: Optional[str] = None
_NEURONS = 8192      # 插件对话用 8K 够（16K 太慢，30s/次）


def _ensure_path() -> Optional[Path]:
    """找到大脑代码目录（含 conductor.py）并加入 sys.path"""
    cands = _candidate_paths()
    cfg = _config_path()
    if cfg is not None:
        cands.append(cfg)
    for p in cands:
        try:
            if (p / "conductor.py").exists():
                sp = str(p)
                if sp not in sys.path:
                    sys.path.insert(0, sp)
                return p
        except OSError:
            continue
    return None


def _get_brain():
    """懒加载新大脑（Conductor + 记忆）"""
    global _brain, _brain_error
    if _brain is not None:
        return _brain
    with _lock:
        if _brain is not None:
            return _brain
        path = _ensure_path()
        if path is None:
            _brain_error = "找不到大脑代码（需 conductor.py）"
            return None
        try:
            from conductor import Conductor  # type: ignore
            b = Conductor(n_neurons=_NEURONS,
                          n_tracts=max(256, _NEURONS // 16),
                          use_llm=True)
            # 载入已学记忆
            mem_file = path / "agent_memory.json"
            if mem_file.exists():
                try:
                    mem = json.loads(mem_file.read_text(encoding="utf-8"))
                    for m in mem:
                        b.teach(m["text"], m["answer"],
                                m.get("source", "oracle"))
                    log.info("载入记忆 %d 条", len(mem))
                except Exception as e:
                    log.warning("记忆载入失败: %s", e)
            _brain = b
            log.info("仿生大脑 v2 已加载: %s (%d 神经元)", path, _NEURONS)
        except Exception as e:
            _brain_error = f"加载失败: {e}"
            log.exception("仿生大脑加载失败")
            return None
    return _brain


def _persist(b):
    """把记忆写回磁盘（供下次载入）"""
    try:
        path = _ensure_path()
        if path is None:
            return
        mem = getattr(b, "memory", [])
        (path / "agent_memory.json").write_text(
            json.dumps([{"text": m["text"], "answer": m["answer"],
                         "source": m["source"]} for m in mem],
                       ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning("记忆保存失败: %s", e)


def _err() -> str:
    return json.dumps({"ok": False, "error": _brain_error or "大脑未就绪"},
                      ensure_ascii=False)


# ==================================================================
# 工具处理
# ==================================================================
def _h_ask(question: str = "", **kw) -> str:
    """★对话：大脑记忆 + LLM 表达"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        r = b.respond(question, steps=3)   # ★steps 从6降到3（省一半时间）
        out = {
            "ok": True,
            "answer": r.get("output") or "（大脑对此不确定）",
            "confidence": r.get("confidence"),
            "recalled": [x["text"][:60] for x in r.get("recalled", [])],
            "brain": {"neurons": b.brain.n, "memory": len(b.memory)},
        }
        return json.dumps(out, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _h_teach(question: str = "", answer: str = "", **kw) -> str:
    """教一条知识"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        ok = b.teach(question, answer, source="oracle")
        _persist(b)
        return json.dumps({"ok": ok, "memory": len(b.memory)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _h_distill(topic: str = "", rounds: int = 2, **kw) -> str:
    """★向 LLM 学习一个主题"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        path = _ensure_path()
        if path is None:
            return _err()
        from llm_distiller import LLMDistiller  # type: ignore
        d = LLMDistiller(b.llm, b, verbose=False)
        r = d.distill(topic, rounds=int(rounds), check=True)
        _persist(b)
        return json.dumps({
            "ok": True,
            "topic": topic,
            "learned": [{"aspect": l["aspect"],
                         "chars": len(l["knowledge"]),
                         "confidence": l["confidence"]}
                        for l in r["learned"]],
            "stored": r["stats"]["stored"],
            "memory_total": len(b.memory),
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _h_recall(query: str = "", top_k: int = 3, **kw) -> str:
    """检索记忆"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        rs = b.recall(query, top_k=int(top_k))
        return json.dumps({
            "ok": True, "query": query,
            "results": [{"score": x["score"], "text": x["text"][:70],
                         "answer": x["answer"][:200]} for x in rs],
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _h_think(text: str = "", steps: int = 8, **kw) -> str:
    """纯思考（不调 LLM 输出）"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        b.perceive(text)
        info = b.think(steps=int(steps))
        return json.dumps({"ok": True, "input": text, **info},
                          ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _h_sleep(**kw) -> str:
    """睡眠巩固"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        s = b.sleep()
        _persist(b)
        return json.dumps({"ok": True, **s, "memory": len(b.memory)},
                          ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _h_state(**kw) -> str:
    """大脑状态"""
    b = _get_brain()
    if b is None:
        return _err()
    try:
        s = b.stats()
        s["ok"] = True
        s["llm"] = {"model": b.llm.model, "available": bool(
            b.llm and b.llm.available)} if getattr(b, "llm", None) else None
        return json.dumps(s, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


# ==================================================================
# 注册入口
# ==================================================================
def register_tools(ctx):
    """Hermes 插件加载器调用此函数"""
    tools = [
        {
            "name": "brain_ask",
            "toolset": "brain",
            "description": "向仿生大脑提问。大脑会检索自己的神经记忆，"
                           "再让语言区表达。适合问它学过的东西。",
            "emoji": "🧠",
            "schema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "问题"},
                },
                "required": ["question"],
            },
            "handler": _h_ask,
        },
        {
            "name": "brain_distill",
            "toolset": "brain",
            "description": "让大脑向 LLM 学习一个主题（自主蒸馏：生成大纲→"
                           "逐点学习→自检→入库）。",
            "emoji": "📚",
            "schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "学习主题"},
                    "rounds": {"type": "integer", "description": "学几个方面，默认2"},
                },
                "required": ["topic"],
            },
            "handler": _h_distill,
        },
        {
            "name": "brain_recall",
            "toolset": "brain",
            "description": "检索大脑记忆，看看它关于某个话题知道什么。",
            "emoji": "🔍",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询"},
                    "top_k": {"type": "integer", "description": "返回条数，默认3"},
                },
                "required": ["query"],
            },
            "handler": _h_recall,
        },
        {
            "name": "brain_teach",
            "toolset": "brain",
            "description": "直接教大脑一条知识（记住问题-答案对）。",
            "emoji": "✍️",
            "schema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "问题"},
                    "answer": {"type": "string", "description": "答案"},
                },
                "required": ["question", "answer"],
            },
            "handler": _h_teach,
        },
        {
            "name": "brain_think",
            "toolset": "brain",
            "description": "让大脑纯思考一段输入（激活扩散，不调语言区）。",
            "emoji": "💭",
            "schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "思考内容"},
                    "steps": {"type": "integer", "description": "tick 数，默认8"},
                },
                "required": ["text"],
            },
            "handler": _h_think,
        },
        {
            "name": "brain_sleep",
            "toolset": "brain",
            "description": "让大脑睡眠巩固（合并可塑量、修剪弱连接）。",
            "emoji": "😴",
            "schema": {"type": "object", "properties": {}},
            "handler": _h_sleep,
        },
        {
            "name": "brain_state",
            "toolset": "brain",
            "description": "查看大脑状态（神经元数、激活、记忆条数、语言区）。",
            "emoji": "📊",
            "schema": {"type": "object", "properties": {}},
            "handler": _h_state,
        },
    ]

    for t in tools:
        try:
            ctx.register_tool(**t)
        except TypeError:
            # 兼容旧签名
            ctx.register_tool(
                name=t["name"], toolset=t["toolset"],
                schema=t["schema"], handler=t["handler"],
                description=t["description"])
    log.info("bio-brain 注册 %d 个工具", len(tools))
    return [t["name"] for t in tools]
