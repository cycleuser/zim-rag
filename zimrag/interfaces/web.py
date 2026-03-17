"""ZIM-RAG Flask Web 接口"""

from flask import Flask, render_template, request, jsonify, Response
import json
from typing import Any, Dict

from ..api import ZIMRAGAPI


def create_app(api: ZIMRAGAPI) -> Flask:
    """创建 Flask 应用"""
    app = Flask(__name__, template_folder="../templates")
    app.api = api

    @app.route("/")
    def index():
        """首页"""
        return render_template("index.html")

    @app.route("/api/ask", methods=["POST"])
    def ask():
        """提问 API"""
        data = request.json
        question = data.get("question", "")
        context_limit = data.get("context_limit", 5)
        model = data.get("model", "llama3")

        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        result = api.ask(question=question, context_limit=context_limit, model=model)

        if result.success:
            return jsonify(result.to_dict())
        else:
            return jsonify({"error": result.error}), 500

    @app.route("/api/ask/stream", methods=["POST"])
    def ask_stream():
        """流式提问 API"""
        data = request.json
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        def generate():
            try:
                for chunk in api.ask_stream(question=question):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.route("/api/chat", methods=["POST"])
    def chat():
        """聊天 API"""
        data = request.json
        messages = data.get("messages", [])
        context_limit = data.get("context_limit", 3)
        model = data.get("model", "llama3")

        result = api.chat(messages=messages, context_limit=context_limit, model=model)

        if result.success:
            return jsonify(result.to_dict())
        else:
            return jsonify({"error": result.error}), 500

    @app.route("/api/zims", methods=["GET"])
    def list_zims():
        """列出 ZIM 文件"""
        result = api.list_zims()
        return jsonify(result.to_dict())

    @app.route("/api/zims", methods=["POST"])
    def add_zim():
        """添加 ZIM 文件"""
        data = request.json
        path = data.get("path", "")

        if not path:
            return jsonify({"error": "路径不能为空"}), 400

        result = api.add_zim(path)
        return jsonify(result.to_dict())

    @app.route("/api/index/build", methods=["POST"])
    def build_index():
        """构建索引"""
        data = request.json
        max_articles = data.get("max_articles", 10000)

        result = api.build_index(max_articles=max_articles)
        return jsonify(result.to_dict())

    @app.route("/api/stats", methods=["GET"])
    def stats():
        """统计信息"""
        result = api.get_stats()
        return jsonify(result.to_dict())

    @app.route("/api/health", methods=["GET"])
    def health():
        """健康检查"""
        result = api.check_health()
        return jsonify(result.to_dict())

    @app.route("/api/models", methods=["GET"])
    def list_models():
        """列出模型"""
        result = api.check_health()
        if result.success:
            return jsonify({"models": result.data.get("models", [])})
        return jsonify({"models": []})

    return app


def launch_web(api: ZIMRAGAPI, host: str = "127.0.0.1", port: int = 5000):
    """启动 Web 服务"""
    app = create_app(api)
    print(f"启动 Web 服务：http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
