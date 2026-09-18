"""
仿生大脑 · Hermes 插件（正确的注册方式）
==========================================
按 Hermes 官方插件约定实现：
  · plugin.yaml   —— manifest（name/provides_tools/kind）
  · __init__.py   —— 包体（保持 import 轻量）
  · tools.py      —— register_tools(ctx) 注册工具

设计铁律：大脑**独立运行**，绝不替换 Hermes 主会话 model。
"""
