"""ZIM-RAG PySide6 图形界面"""

import sys
import threading
from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QProgressBar,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolBar,
    QAction,
    QSystemTrayIcon,
    QMenu,
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QFont, QIcon, QTextCursor


class QuestionWorker(QObject):
    """提问工作线程"""

    finished = Signal(str)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, api, question: str, context_limit: int, model: str):
        super().__init__()
        self.api = api
        self.question = question
        self.context_limit = context_limit
        self.model = model

    def run(self):
        try:
            result = self.api.ask(
                question=self.question,
                context_limit=self.context_limit,
                model=self.model,
            )
            if result.success:
                self.finished.emit(result.data.get("answer", ""))
            else:
                self.error.emit(result.error or "未知错误")
        except Exception as e:
            self.error.emit(str(e))


class IndexWorker(QObject):
    """索引构建工作线程"""

    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, api, zim_paths: List[str], max_articles: int):
        super().__init__()
        self.api = api
        self.zim_paths = zim_paths
        self.max_articles = max_articles

    def run(self):
        try:
            # 添加 ZIM 文件
            for path in self.zim_paths:
                self.progress.emit(f"加载：{Path(path).name}")
                self.api.add_zim(path)

            # 构建索引
            self.progress.emit("开始构建索引...")
            result = self.api.build_index(max_articles=self.max_articles)

            if result.success:
                self.finished.emit(result.data)
            else:
                self.error.emit(result.error or "索引构建失败")
        except Exception as e:
            self.error.emit(str(e))


class ZIMRAGWindow(QMainWindow):
    """主窗口"""

    def __init__(self, api):
        super().__init__()
        self.api = api
        self.worker_thread = None
        self.current_worker = None

        self._init_ui()
        self._connect_signals()
        self._load_zims()

    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("ZIM-RAG 知识库问答系统 v1.0")
        self.setMinimumSize(1000, 700)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部工具栏
        self._create_toolbar()

        # ZIM 文件管理区
        zim_group = QGroupBox("ZIM 知识库")
        zim_layout = QVBoxLayout(zim_group)

        zim_file_layout = QHBoxLayout()
        self.zim_list = QTextEdit()
        self.zim_list.setMaximumHeight(80)
        self.zim_list.setReadOnly(True)
        self.zim_list.setPlaceholderText("已加载的 ZIM 文件将显示在这里...")
        zim_file_layout.addWidget(QLabel("已加载:"))
        zim_file_layout.addWidget(self.zim_list, 1)

        btn_add_zim = QPushButton("添加 ZIM 文件")
        btn_add_zim.clicked.connect(self._add_zim)
        btn_build_index = QPushButton("构建索引")
        btn_build_index.clicked.connect(self._build_index)
        zim_file_layout.addWidget(btn_add_zim)
        zim_file_layout.addWidget(btn_build_index)

        zim_layout.addLayout(zim_file_layout)
        main_layout.addWidget(zim_group)

        # 分割器
        splitter = QSplitter(Qt.Vertical)

        # 上部：问题输入区
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self._update_models()
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(QLabel("上下文数量:"))
        self.context_spin = QComboBox()
        self.context_spin.addItems(["3", "5", "10", "15"])
        self.context_spin.setCurrentIndex(1)
        model_layout.addWidget(self.context_spin)
        model_layout.addStretch()
        input_layout.addLayout(model_layout)

        # 问题输入
        input_layout.addWidget(QLabel("问题:"))
        self.question_input = QTextEdit()
        self.question_input.setMaximumHeight(100)
        self.question_input.setPlaceholderText("输入您的问题，按 Ctrl+Enter 发送...")
        self.question_input.installEventFilter(self)
        input_layout.addWidget(self.question_input)

        # 发送按钮
        btn_layout = QHBoxLayout()
        self.btn_ask = QPushButton("🔍 提问")
        self.btn_ask.setMinimumHeight(40)
        self.btn_ask.clicked.connect(self._ask_question)
        btn_layout.addWidget(self.btn_ask)
        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)

        splitter.addWidget(input_widget)

        # 下部：答案显示区
        answer_widget = QWidget()
        answer_layout = QVBoxLayout(answer_widget)
        answer_layout.setContentsMargins(0, 0, 0, 0)

        answer_layout.addWidget(QLabel("答案:"))
        self.answer_output = QTextEdit()
        self.answer_output.setReadOnly(True)
        self.answer_output.setPlaceholderText("答案将显示在这里...")
        font = QFont("Consolas", 10)
        self.answer_output.setFont(font)
        answer_layout.addWidget(self.answer_output)

        # 来源表格
        answer_layout.addWidget(QLabel("参考来源:"))
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(2)
        self.sources_table.setHorizontalHeaderLabels(["标题", "来源"])
        self.sources_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sources_table.setMaximumHeight(120)
        answer_layout.addWidget(self.sources_table)

        splitter.addWidget(answer_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar.addPermanentWidget(self.progress_bar, 1)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 动作
        action_chat = QAction("💬 聊天模式", self)
        action_chat.triggered.connect(self._open_chat)
        toolbar.addAction(action_chat)

        action_stats = QAction("📊 统计信息", self)
        action_stats.triggered.connect(self._show_stats)
        toolbar.addAction(action_stats)

        action_health = QAction("❤️ 健康检查", self)
        action_health.triggered.connect(self._check_health)
        toolbar.addAction(action_health)

        toolbar.addSeparator()

        action_clear = QAction("🗑️ 清空", self)
        action_clear.triggered.connect(self._clear_output)
        toolbar.addAction(action_clear)

        action_export = QAction("💾 导出", self)
        action_export.triggered.connect(self._export_answer)
        toolbar.addAction(action_export)

    def _connect_signals(self):
        """连接信号"""
        pass

    def _load_zims(self):
        """加载已保存的 ZIM 文件"""
        result = self.api.list_zims()
        if result.success and result.data:
            zims_text = "\n".join([f["name"] for f in result.data])
            self.zim_list.setText(zims_text)

    def _update_models(self):
        """更新模型列表"""
        self.model_combo.clear()
        result = self.api.check_health()
        if result.success and result.data.get("models"):
            self.model_combo.addItems(result.data["models"])
        else:
            self.model_combo.addItem("llama3")

    def _add_zim(self):
        """添加 ZIM 文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择 ZIM 文件", "", "ZIM Files (*.zim)"
        )
        if files:
            for f in files:
                result = self.api.add_zim(f)
                if result.success:
                    current = self.zim_list.toPlainText()
                    if current:
                        self.zim_list.setText(current + "\n" + Path(f).name)
                    else:
                        self.zim_list.setText(Path(f).name)
                    self.statusBar.showMessage(f"已添加：{Path(f).name}")
                else:
                    QMessageBox.warning(self, "添加失败", result.error)

    def _build_index(self):
        """构建索引"""
        zim_text = self.zim_list.toPlainText()
        if not zim_text.strip():
            QMessageBox.warning(self, "提示", "请先添加 ZIM 文件")
            return

        reply = QMessageBox.question(
            self,
            "确认",
            "构建索引可能需要较长时间，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._start_index_worker()

    def _start_index_worker(self):
        """启动索引工作线程"""
        zim_text = self.zim_list.toPlainText()
        zim_paths = [line.strip() for line in zim_text.split("\n") if line.strip()]

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.btn_ask.setEnabled(False)

        self.worker_thread = QThread()
        self.current_worker = IndexWorker(self.api, zim_paths, 10000)
        self.current_worker.moveToThread(self.worker_thread)

        self.current_worker.progress.connect(
            lambda msg: self.statusBar.showMessage(msg)
        )
        self.current_worker.finished.connect(self._on_index_finished)
        self.current_worker.error.connect(self._on_index_error)
        self.current_worker.finished.connect(self.worker_thread.quit)
        self.current_worker.error.connect(self.worker_thread.quit)

        self.worker_thread.started.connect(self.current_worker.run)
        self.worker_thread.start()

    def _on_index_finished(self, stats):
        """索引完成"""
        self.progress_bar.setVisible(False)
        self.btn_ask.setEnabled(True)

        indexed = stats.get("total_indexed", 0)
        QMessageBox.information(
            self,
            "索引完成",
            f"成功索引 {indexed:,} 个文档块\n\n{stats.get('by_file', {})}",
        )
        self._update_models()

    def _on_index_error(self, error):
        """索引错误"""
        self.progress_bar.setVisible(False)
        self.btn_ask.setEnabled(True)
        QMessageBox.critical(self, "索引失败", error)

    def _ask_question(self):
        """提问"""
        question = self.question_input.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "提示", "请输入问题")
            return

        self.btn_ask.setEnabled(False)
        self.answer_output.setText("正在思考中...")
        self.sources_table.setRowCount(0)

        self.worker_thread = QThread()
        self.current_worker = QuestionWorker(
            self.api,
            question=question,
            context_limit=int(self.context_spin.currentText()),
            model=self.model_combo.currentText(),
        )
        self.current_worker.moveToThread(self.worker_thread)

        self.current_worker.finished.connect(self._on_answer_finished)
        self.current_worker.error.connect(self._on_answer_error)
        self.current_worker.finished.connect(self.worker_thread.quit)
        self.current_worker.error.connect(self.worker_thread.quit)

        self.worker_thread.started.connect(self.current_worker.run)
        self.worker_thread.start()

    def _on_answer_finished(self, answer):
        """回答完成"""
        self.btn_ask.setEnabled(True)
        self.answer_output.setText(answer)
        self.statusBar.showMessage("回答完成")

    def _on_answer_error(self, error):
        """回答错误"""
        self.btn_ask.setEnabled(True)
        self.answer_output.setText(f"错误：{error}")
        QMessageBox.critical(self, "提问失败", error)

    def _open_chat(self):
        """打开聊天模式"""
        QMessageBox.information(self, "提示", "聊天模式开发中...")

    def _show_stats(self):
        """显示统计"""
        result = self.api.get_stats()
        if result.success:
            stats = result.data
            msg = f"""系统统计

ZIM 文件：{stats.get("zim_files", {}).get("loaded_files", 0)}
总文章数：{stats.get("zim_files", {}).get("total_articles", 0):,}
总大小：{stats.get("zim_files", {}).get("total_size_gb", 0):.2f} GB

模型：{stats.get("model", "N/A")}
Ollama 状态：{"正常" if stats.get("ollama_healthy") else "异常"}
            """
            QMessageBox.information(self, "统计信息", msg)

    def _check_health(self):
        """健康检查"""
        result = self.api.check_health()
        if result.success:
            models = result.data.get("models", [])
            msg = f"Ollama 状态：正常\n\n可用模型:\n" + "\n".join(models)
            QMessageBox.information(self, "健康状态", msg)
        else:
            QMessageBox.warning(self, "健康检查", f"Ollama 服务异常:\n{result.error}")

    def _clear_output(self):
        """清空输出"""
        self.answer_output.clear()
        self.sources_table.setRowCount(0)
        self.statusBar.showMessage("已清空")

    def _export_answer(self):
        """导出答案"""
        answer = self.answer_output.toPlainText()
        if not answer:
            QMessageBox.warning(self, "提示", "没有可导出的内容")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出答案", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(answer)
            self.statusBar.showMessage(f"已导出到：{path}")

    def eventFilter(self, obj, event):
        """事件过滤"""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent

        if obj == self.question_input and event.type() == QEvent.KeyPress:
            key_event = event
            if (
                key_event.key() == Qt.Key_Return
                and key_event.modifiers() == Qt.ControlModifier
            ):
                self._ask_question()
                return True

        return super().eventFilter(obj, event)


def launch_gui(api, no_web: bool = False):
    """启动 GUI"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ZIMRAGWindow(api)
    window.show()

    sys.exit(app.exec())
