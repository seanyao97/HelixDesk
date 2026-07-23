import sys, os
from datetime import datetime, date
from calendar import monthcalendar

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame, QScrollArea, QGridLayout, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog,
    QSplitter, QInputDialog, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal

from helixdesk import database as db


STYLE = """
QMainWindow, QWidget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 13px; color: #1e202e; }
QMainWindow { background: #f5f6fa; }
#navPanel { background: #1a1d2e; min-width: 200px; max-width: 200px; }
#navPanel QPushButton { text-align: left; padding: 10px 16px; border: none; border-radius: 6px; color: #8b8fa3; font-size: 13px; margin: 2px 8px; }
#navPanel QPushButton:hover { background: #25283d; color: #fff; }
#navPanel QPushButton:checked { background: #2d3150; color: #fff; font-weight: 600; }
QPushButton#btnPrimary { background: #4f6ef7; color: #fff; border: none; border-radius: 6px; padding: 7px 18px; font-weight: 500; }
QPushButton#btnPrimary:hover { background: #3b56d9; }
QPushButton#btnSecondary { background: #fff; color: #1e202e; border: 1px solid #e2e5ec; border-radius: 6px; padding: 6px 14px; }
QPushButton#btnSecondary:hover { border-color: #4f6ef7; color: #4f6ef7; background: #f8f9ff; }
QPushButton#btnDanger { background: none; color: #ef4444; border: none; padding: 4px 10px; border-radius: 4px; }
QPushButton#btnDanger:hover { background: #fef2f2; }
QLineEdit, QTextEdit, QComboBox { border: 1px solid #e2e5ec; border-radius: 6px; padding: 7px 10px; background: #fff; font-size: 13px; }
QLineEdit:focus, QTextEdit:focus { border-color: #4f6ef7; box-shadow: 0 0 0 3px rgba(79,110,247,0.1); }
QListWidget { border: none; background: transparent; font-size: 13px; }
QListWidget::item { padding: 8px 12px; border-radius: 6px; margin: 1px 4px; }
QListWidget::item:hover { background: #f0f4ff; }
QListWidget::item:selected { background: #eef1ff; color: #4f6ef7; font-weight: 500; }
QScrollBar:vertical { width: 4px; background: transparent; }
QScrollBar::handle:vertical { background: #d0d3dc; border-radius: 2px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #b0b3be; }
QScrollArea { border: none; }
QSplitter::handle { background: #e8eaf0; width: 1px; }
"""


def status_label(s):
    return {"draft": "草稿", "submitted": "已提交", "archived": "已归档"}.get(s, s)


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


class ProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumWidth(380)
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("项目名称")
        layout.addRow("名称 *", self.name_input)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("项目描述（可选）")
        self.desc_input.setMaximumHeight(80)
        layout.addRow("描述", self.desc_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
        self.name_input.setFocus()


class ExperimentDialog(QDialog):
    def __init__(self, parent=None, experiment=None):
        super().__init__(parent)
        self.exp = experiment
        self.setWindowTitle("编辑实验" if experiment else "新建实验")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("实验标题")
        layout.addRow("标题 *", self.title_input)
        self.purpose_input = QTextEdit()
        self.purpose_input.setPlaceholderText("实验目的")
        self.purpose_input.setMaximumHeight(60)
        layout.addRow("目的", self.purpose_input)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addRow("日期", self.date_input)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("实验室/房间")
        layout.addRow("地点", self.location_input)
        self.project_combo = QComboBox()
        for p in db.list_projects():
            self.project_combo.addItem(p["name"], p["id"])
        layout.addRow("所属项目", self.project_combo)
        if experiment:
            self.title_input.setText(experiment.get("title", ""))
            self.purpose_input.setPlainText(experiment.get("purpose", ""))
            if experiment.get("date"):
                self.date_input.setDate(QDate.fromString(experiment["date"], "yyyy-MM-dd"))
            self.location_input.setText(experiment.get("location", ""))
            idx = self.project_combo.findData(experiment.get("project_id"))
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
        self.title_input.setFocus()

    def accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "提示", "请输入实验标题")
            return
        super().accept()


class StepDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加步骤")
        self.setMinimumWidth(380)
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("步骤标题")
        layout.addRow("标题 *", self.title_input)
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("操作细节、注意事项")
        self.content_input.setMaximumHeight(100)
        layout.addRow("说明", self.content_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
        self.title_input.setFocus()

    def accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "提示", "请输入步骤标题")
            return
        super().accept()


# Calendar View
class CalendarView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cy = datetime.now().year
        self.cm = datetime.now().month
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        nav = QHBoxLayout()
        title = QLabel("📅 计划表")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        nav.addWidget(title)
        nav.addStretch()
        self.mlbl = QLabel()
        self.mlbl.setStyleSheet("font-size: 16px; font-weight: 600; min-width: 140px;")
        nav.addWidget(self.mlbl)
        prev = QPushButton("‹")
        prev.setFixedSize(32, 32)
        prev.clicked.connect(lambda: self.nav(-1))
        nav.addWidget(prev)
        nxt = QPushButton("›")
        nxt.setFixedSize(32, 32)
        nxt.clicked.connect(lambda: self.nav(1))
        nav.addWidget(nxt)
        td = QPushButton("今天")
        td.setObjectName("btnSecondary")
        td.clicked.connect(self.go_today)
        nav.addWidget(td)
        layout.addLayout(nav)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.cw = QWidget()
        self.cg = QGridLayout(self.cw)
        self.cg.setSpacing(1)
        scroll.setWidget(self.cw)
        layout.addWidget(scroll, 1)
        self.render()

    def nav(self, d):
        self.cm += d
        if self.cm > 12:
            self.cm = 1; self.cy += 1
        elif self.cm < 1:
            self.cm = 12; self.cy -= 1
        self.render()

    def go_today(self):
        self.cy = datetime.now().year
        self.cm = datetime.now().month
        self.render()

    def render(self):
        while self.cg.count():
            w = self.cg.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        mnames = ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]
        self.mlbl.setText(f"{self.cy}年 {mnames[self.cm-1]}")
        for i, d in enumerate(["日","一","二","三","四","五","六"]):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #9ea2b5; padding: 6px;")
            self.cg.addWidget(lbl, 0, i)
        ms = f"{self.cy}-{self.cm:02d}"
        exps = db.list_experiments()
        plans = db.list_plans()
        dd = {}
        cal = monthcalendar(self.cy, self.cm)
        for w in cal:
            for d in w:
                if d:
                    ds = f"{ms}-{d:02d}"
                    dd[ds] = {"exps": [], "todos": [], "dones": []}
        for e in exps:
            if e["date"] and e["date"] in dd:
                dd[e["date"]]["exps"].append(e)
        for p in plans:
            if p["date"] and p["date"] in dd:
                if p["done"]: dd[p["date"]]["dones"].append(p)
                else: dd[p["date"]]["todos"].append(p)
        td = today_str()
        for wi, w in enumerate(cal):
            for di, d in enumerate(w):
                if d == 0:
                    cell = QLabel(); cell.setStyleSheet("background: #fafbfc;")
                    self.cg.addWidget(cell, wi+1, di)
                    continue
                ds = f"{ms}-{d:02d}"
                data = dd.get(ds, {"exps":[],"todos":[],"dones":[]})
                cell = QWidget()
                bg = "#eef1ff" if ds == td else "#fff"
                cell.setStyleSheet(f"background: {bg};")
                cl = QVBoxLayout(cell)
                cl.setContentsMargins(4,2,4,2)
                cl.setSpacing(1)
                n = QLabel(str(d))
                ns = "font-size: 12px; font-weight: 700; color: #4f6ef7; padding: 2px 0;" if ds == td else "font-size: 12px; font-weight: 600; padding: 2px 0;"
                n.setStyleSheet(ns)
                cl.addWidget(n)
                for e in data["exps"]:
                    lbl = QLabel(e["title"][:10])
                    lbl.setStyleSheet("background: #eef1ff; color: #4f6ef7; padding: 1px 4px; border-radius: 3px; font-size: 10px;")
                    cl.addWidget(lbl)
                for p in data["todos"]:
                    lbl = QLabel(p["title"][:10])
                    lbl.setStyleSheet("background: #fffbeb; color: #f59e0b; padding: 1px 4px; border-radius: 3px; font-size: 10px;")
                    cl.addWidget(lbl)
                for p in data["dones"]:
                    lbl = QLabel("✓ "+p["title"][:8])
                    lbl.setStyleSheet("background: #ecfdf5; color: #22c55e; padding: 1px 4px; border-radius: 3px; font-size: 10px;")
                    cl.addWidget(lbl)
                cl.addStretch()
                cell.setCursor(Qt.PointingHandCursor)
                cell.mousePressEvent = lambda e, ds=ds: self.click_day(ds)
                self.cg.addWidget(cell, wi+1, di)

    def click_day(self, ds):
        title, ok = QInputDialog.getText(self, "添加事项", f"在 {ds} 添加：")
        if ok and title.strip():
            db.add_plan(ds, title.strip())
            self.render()

class ExperimentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        header = QHBoxLayout()
        title = QLabel("🧪 实验")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        header.addWidget(title); header.addStretch()
        self.new_exp_btn = QPushButton("+ 新建实验")
        self.new_exp_btn.setObjectName("btnPrimary")
        self.new_exp_btn.clicked.connect(self.show_new_exp)
        header.addWidget(self.new_exp_btn)
        self.new_proj_btn = QPushButton("+ 新建项目")
        self.new_proj_btn.setObjectName("btnSecondary")
        self.new_proj_btn.clicked.connect(self.show_new_proj)
        header.addWidget(self.new_proj_btn)
        layout.addLayout(header)
        fl = QHBoxLayout()
        layout.addLayout(fl)
        splitter = QSplitter(Qt.Horizontal)
        lw = QWidget(); ll = QVBoxLayout(lw); ll.setContentsMargins(0,0,0,0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        self.ec = QWidget(); self.el = QVBoxLayout(self.ec); self.el.setSpacing(8); self.el.addStretch()
        scroll.setWidget(self.ec); ll.addWidget(scroll)
        splitter.addWidget(lw)
        self.dw = QWidget(); self.dl = QVBoxLayout(self.dw); self.dl.setContentsMargins(16,0,0,0)
        ds = QScrollArea(); ds.setWidgetResizable(True); ds.setFrameShape(QFrame.NoFrame)
        self.dc = QWidget(); self.di = QVBoxLayout(self.dc); ds.setWidget(self.dc); self.dl.addWidget(ds)
        splitter.addWidget(self.dw); splitter.setSizes([400, 500])
        layout.addWidget(splitter, 1)
        self.fbtns = []
        self.fil = fl

    def load_data(self):
        self.load_filters(); self.load_exps()

    def load_filters(self):
        for b in self.fbtns:
            self.fil.removeWidget(b); b.deleteLater()
        self.fbtns.clear()
        win = self.window()
        pid = win.current_project_id if hasattr(win, "current_project_id") else None
        btn = QPushButton("全部"); btn.setCheckable(True); btn.setChecked(pid is None)
        btn.clicked.connect(lambda: self.filter_by(None))
        self.fil.addWidget(btn); self.fbtns.append(btn)
        for p in db.list_projects():
            btn = QPushButton(p["name"]); btn.setCheckable(True); btn.setChecked(p["id"] == pid)
            btn.clicked.connect(lambda checked, x=p["id"]: self.filter_by(x))
            self.fil.addWidget(btn); self.fbtns.append(btn)
        self.fil.addStretch()

    def filter_by(self, pid):
        self.window().current_project_id = pid
        for b in self.fbtns:
            b.setChecked(False)
        self.sender().setChecked(True)
        self.load_exps()

    def load_exps(self):
        while self.el.count():
            w = self.el.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        win = self.window()
        pid = win.current_project_id if hasattr(win,"current_project_id") else None
        exps = db.list_experiments(pid)
        for e in exps:
            card = self._make_card(e)
            self.el.addWidget(card)
        self.el.addStretch()
        if not exps:
            lbl = QLabel("暂无实验记录"); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #9ea2b5; padding: 40px;"); self.el.addWidget(lbl)

    def _make_card(self, e):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("ExperimentCard{background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:14px;}ExperimentCard:hover{border-color:#4f6ef7;}")
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card); layout.setContentsMargins(14,12,14,12); layout.setSpacing(4)
        title = QLabel(e["title"]); title.setStyleSheet("font-size:14px;font-weight:600;"); layout.addWidget(title)
        meta = QLabel(f'{e["date"] or ""}  ·  {e.get("project_name","")}')
        meta.setStyleSheet("font-size:12px;color:#6b7085;"); layout.addWidget(meta)
        if e.get("purpose"):
            p = QLabel(e["purpose"]); p.setStyleSheet("font-size:12px;color:#9ea2b5;"); p.setWordWrap(True); p.setMaximumHeight(36)
            layout.addWidget(p)
        s = e["status"]; colors = {"draft":("#eef1ff","#4f6ef7"),"submitted":("#fffbeb","#f59e0b"),"archived":("#ecfdf5","#22c55e")}
        bg, fg = colors.get(s,("#eef1ff","#4f6ef7"))
        st = QLabel(status_label(s)); st.setStyleSheet(f"background:{bg};color:{fg};padding:1px 8px;border-radius:8px;font-size:11px;")
        st.setFixedWidth(60); layout.addWidget(st)
        card.mousePressEvent = lambda ev, eid=e["id"]: self.show_detail(eid)
        return card

    def show_detail(self, eid):
        exp = db.get_experiment(eid)
        if not exp: return
        while self.di.count():
            w = self.di.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        title = QLabel(exp["title"]); title.setStyleSheet("font-size:18px;font-weight:700;")
        self.di.addWidget(title)
        meta = QLabel(f"📅 {exp['date'] or ''}  📍 {exp['location'] or '未指定'}  [{status_label(exp['status'])}]")
        meta.setStyleSheet("color:#6b7085;font-size:12px;"); self.di.addWidget(meta)
        if exp.get("purpose"):
            pu = QLabel(exp["purpose"]); pu.setStyleSheet("background:#eef1ff;padding:10px 14px;border-radius:6px;border-left:3px solid #4f6ef7;")
            pu.setWordWrap(True); self.di.addWidget(pu)
        # Steps
        st = QLabel(f"📋 步骤 ({len(exp['steps'])})"); st.setStyleSheet("font-size:14px;font-weight:600;margin-top:12px;")
        self.di.addWidget(st)
        asb = QPushButton("+ 添加步骤"); asb.setObjectName("btnSecondary")
        asb.clicked.connect(lambda: self.add_step(eid)); self.di.addWidget(asb)
        if exp["steps"]:
            for i, s in enumerate(exp["steps"]):
                sw = self._make_step(s, i+1)
                sw.deleted.connect(lambda x=s["id"]: (db.delete_step(x), self.show_detail(eid)))
                self.di.addWidget(sw)
        else:
            self.di.addWidget(QLabel("暂无步骤"))
        # Results
        rt = QLabel(f"📊 结果 ({len(exp['results'])})"); rt.setStyleSheet("font-size:14px;font-weight:600;margin-top:12px;")
        self.di.addWidget(rt)
        arb = QPushButton("+ 记录结果"); arb.setObjectName("btnSecondary")
        arb.clicked.connect(lambda: self.add_result(eid)); self.di.addWidget(arb)
        for r in exp["results"]:
            rw = self._make_result(r)
            rw.deleted.connect(lambda x=r["id"]: (db.delete_result(x), self.show_detail(eid)))
            self.di.addWidget(rw)
        # Actions
        act = QHBoxLayout()
        eb = QPushButton("✏️ 编辑"); eb.setObjectName("btnSecondary")
        eb.clicked.connect(lambda: self.edit_exp(eid)); act.addWidget(eb)
        sc = QComboBox(); sc.addItems(["草稿","已提交","已归档"])
        smap = {"草稿":"draft","已提交":"submitted","已归档":"archived"}
        sc.setCurrentText([k for k,v in smap.items() if v==exp["status"]][0])
        sc.currentTextChanged.connect(lambda t: db.update_experiment(eid,{"status":smap[t]})); act.addWidget(sc)
        apb = QPushButton("📋 加入计划"); apb.setObjectName("btnSecondary")
        apb.clicked.connect(lambda: (db.add_plan(today_str(),exp["title"],eid), QMessageBox.information(self,"提示","已加入今日计划")))
        act.addWidget(apb)
        # Export
        exb = QPushButton("⬇ 导出"); exb.setObjectName("btnSecondary")
        exb.clicked.connect(lambda: self.export_exp(eid)); act.addWidget(exb)
        # Run logs
        rlb = QPushButton("📝 运行日志"); rlb.setObjectName("btnSecondary")
        rlb.clicked.connect(lambda: self.show_logs(eid)); act.addWidget(rlb)
        # Params
        pmb = QPushButton("⚙ 参数"); pmb.setObjectName("btnSecondary")
        pmb.clicked.connect(lambda: self.show_params(eid)); act.addWidget(pmb)
        self.di.addLayout(act)
        self.di.addStretch()

    def _make_step(self, s, i):
        sw = QFrame()
        sw.setStyleSheet("StepWidget{background:#fff;border:1px solid #e8eaf0;border-radius:8px;padding:10px;margin:4px 0;}")
        layout = QVBoxLayout(sw); layout.setContentsMargins(12,10,12,10)
        h = QHBoxLayout()
        n = QLabel(f"{i}. {s['title']}"); n.setStyleSheet("font-weight:600;font-size:13px;"); h.addWidget(n); h.addStretch()
        db2 = QPushButton("删除"); db2.setObjectName("btnDanger")
        db2.clicked.connect(lambda: sw.deleted.emit() if hasattr(sw,'deleted') else None); h.addWidget(db2)
        layout.addLayout(h)
        if s.get("content"):
            c = QLabel(s["content"]); c.setStyleSheet("font-size:12px;color:#6b7085;"); c.setWordWrap(True); layout.addWidget(c)
        sw.deleted = Signal()
        return sw

    def _make_result(self, r):
        rw = QFrame()
        rw.setStyleSheet("ResultWidget{background:#fafbfc;border:1px dashed #e8eaf0;border-radius:6px;padding:8px;margin:2px 0;}")
        layout = QHBoxLayout(rw); layout.setContentsMargins(10,6,10,6)
        t = QLabel(r["content"]); t.setWordWrap(True); t.setStyleSheet("font-size:12px;"); layout.addWidget(t,1)
        db2 = QPushButton("✕"); db2.setFixedSize(20,20); db2.setStyleSheet("border:none;color:#9ea2b5;font-size:12px;")
        db2.clicked.connect(lambda: rw.deleted.emit() if hasattr(rw,'deleted') else None); layout.addWidget(db2)
        rw.deleted = Signal()
        return rw

    def show_new_proj(self):
        dlg = ProjectDialog(self)
        if dlg.exec():
            db.create_project(dlg.name_input.text().strip(), dlg.desc_input.toPlainText().strip())
            self.load_data()

    def show_new_exp(self):
        dlg = ExperimentDialog(self)
        if dlg.exec():
            db.create_experiment(dlg.project_combo.currentData(), dlg.title_input.text().strip(),
                dlg.purpose_input.toPlainText().strip(), dlg.date_input.date().toString("yyyy-MM-dd"),
                dlg.location_input.text().strip())
            self.load_data()

    def edit_exp(self, eid):
        exp = db.get_experiment(eid)
        if not exp: return
        dlg = ExperimentDialog(self, exp)
        if dlg.exec():
            db.update_experiment(eid,{"title":dlg.title_input.text().strip(),
                "purpose":dlg.purpose_input.toPlainText().strip(),
                "date":dlg.date_input.date().toString("yyyy-MM-dd"),
                "location":dlg.location_input.text().strip()})
            self.show_detail(eid); self.load_exps()

    def add_step(self, eid):
        dlg = StepDialog(self)
        if dlg.exec():
            db.add_step(eid, dlg.title_input.text().strip(), dlg.content_input.toPlainText().strip())
            self.show_detail(eid)

    def add_result(self, eid):
        content, ok = QInputDialog.getMultiLineText(self, "记录结果", "输入结果内容：")
        if ok and content.strip():
            db.add_result(eid, content.strip())
            self.show_detail(eid)

    def export_exp(self, eid):
        md = db.export_markdown(eid)
        exp = db.get_experiment(eid)
        if not exp: return
        fp, _ = QFileDialog.getSaveFileName(self, "导出实验", exp["title"].replace("/","_")+".md", "Markdown (*.md)")
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(md)
            QMessageBox.information(self, "导出成功", f"已导出到：{fp}")

    def show_logs(self, eid):
        logs = db.list_run_logs(eid)
        dlg = QDialog(self); dlg.setWindowTitle("运行日志"); dlg.setMinimumSize(500,400)
        layout = QVBoxLayout(dlg)
        ab = QPushButton("+ 添加运行日志"); ab.setObjectName("btnPrimary")
        ab.clicked.connect(lambda: self.add_log(eid, dlg)); layout.addWidget(ab)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        w = QWidget(); wl = QVBoxLayout(w)
        for log in logs:
            card = QFrame()
            card.setStyleSheet("QFrame{background:#fff;border:1px solid #e8eaf0;border-radius:8px;padding:10px;margin:4px 0;}")
            cl = QVBoxLayout(card)
            cl.addWidget(QLabel(f"v{log['version']} - {log.get('run_date','')}"))
            if log.get("observations"): cl.addWidget(QLabel(f"观察：{log['observations']}"))
            if log.get("deviations"): cl.addWidget(QLabel(f"偏差：{log['deviations']}"))
            if log.get("conclusion"): cl.addWidget(QLabel(f"结论：{log['conclusion']}"))
            dl = QPushButton("删除"); dl.setObjectName("btnDanger")
            dl.clicked.connect(lambda x=log["id"]: (db.delete_run_log(x), dlg.close(), self.show_logs(eid)))
            cl.addWidget(dl); wl.addWidget(card)
        if not logs: wl.addWidget(QLabel("暂无运行日志"))
        wl.addStretch(); scroll.setWidget(w); layout.addWidget(scroll,1)
        cb = QPushButton("关闭"); cb.setObjectName("btnSecondary"); cb.clicked.connect(dlg.close); layout.addWidget(cb)
        dlg.exec()

    def add_log(self, eid, pd):
        dlg = QDialog(pd); dlg.setWindowTitle("添加运行日志"); dlg.setMinimumWidth(400)
        layout = QFormLayout(dlg)
        di = QDateEdit(); di.setCalendarPopup(True); di.setDate(QDate.currentDate()); layout.addRow("日期", di)
        oi = QTextEdit(); oi.setPlaceholderText("实验观察结果..."); oi.setMaximumHeight(60); layout.addRow("观察", oi)
        dvi = QTextEdit(); dvi.setPlaceholderText("偏差或异常..."); dvi.setMaximumHeight(60); layout.addRow("偏差", dvi)
        ci = QTextEdit(); ci.setPlaceholderText("结论..."); ci.setMaximumHeight(60); layout.addRow("结论", ci)
        btns = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject); layout.addRow(btns)
        if dlg.exec():
            logs = db.list_run_logs(eid)
            nv = (logs[0]["version"] + 1) if logs else 1
            db.add_run_log(eid, oi.toPlainText().strip(), dvi.toPlainText().strip(), ci.toPlainText().strip(), nv, di.date().toString("yyyy-MM-dd"))
            pd.close(); self.show_logs(eid)

    def show_params(self, eid):
        params = db.list_params(eid)
        dlg = QDialog(self); dlg.setWindowTitle("参数管理"); dlg.setMinimumSize(450,350)
        layout = QVBoxLayout(dlg)
        ab = QPushButton("+ 添加参数"); ab.setObjectName("btnPrimary")
        ab.clicked.connect(lambda: self.add_param(eid, dlg)); layout.addWidget(ab)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        w = QWidget(); wl = QVBoxLayout(w)
        for p in params:
            card = QFrame()
            card.setStyleSheet("QFrame{background:#fff;border:1px solid #e8eaf0;border-radius:6px;padding:8px;margin:2px 0;}")
            cl = QHBoxLayout(card)
            cl.addWidget(QLabel(f"{p['name']} = {p['value']} {p['unit']}")); cl.addStretch()
            dl = QPushButton("✕"); dl.setFixedSize(20,20); dl.setStyleSheet("border:none;color:#9ea2b5;")
            dl.clicked.connect(lambda x=p["id"]: (db.delete_param(x), dlg.close(), self.show_params(eid)))
            cl.addWidget(dl); wl.addWidget(card)
        if not params: wl.addWidget(QLabel("暂无参数"))
        wl.addStretch(); scroll.setWidget(w); layout.addWidget(scroll,1)
        cb = QPushButton("关闭"); cb.setObjectName("btnSecondary"); cb.clicked.connect(dlg.close); layout.addWidget(cb)
        dlg.exec()

    def add_param(self, eid, pd):
        name, ok = QInputDialog.getText(self, "添加参数", "参数名称：")
        if ok and name.strip():
            val, ok2 = QInputDialog.getText(self, "添加参数", "参数值：")
            if ok2:
                unit, ok3 = QInputDialog.getText(self, "添加参数", "单位（可选）：")
                if ok3:
                    db.add_param(eid, name.strip(), val.strip(), unit.strip())
                    pd.close(); self.show_params(eid)

class MaterialView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(20,16,20,16)
        header = QHBoxLayout()
        title = QLabel("🧫 材料库"); title.setStyleSheet("font-size:18px;font-weight:700;")
        header.addWidget(title); header.addStretch()
        self.ab = QPushButton("+ 添加材料"); self.ab.setObjectName("btnPrimary")
        self.ab.clicked.connect(self.add_mat); header.addWidget(self.ab)
        layout.addLayout(header)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        self.mw = QWidget(); self.ml = QVBoxLayout(self.mw); scroll.setWidget(self.mw); layout.addWidget(scroll,1)

    def load_data(self):
        while self.ml.count():
            w = self.ml.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        mats = db.list_materials()
        if not mats:
            lbl = QLabel("材料库为空"); lbl.setAlignment(Qt.AlignCenter); lbl.setStyleSheet("color:#9ea2b5;padding:40px;")
            self.ml.addWidget(lbl)
        else:
            flow = QHBoxLayout(); flow.setSpacing(6)
            for i, m in enumerate(mats):
                tag = QPushButton(m["name"])
                tag.setStyleSheet("QPushButton{background:#eef1ff;color:#4f6ef7;border:none;border-radius:14px;padding:5px 14px;font-size:13px;font-weight:500;}QPushButton:hover{background:#dce3ff;}")
                tag.setCursor(Qt.PointingHandCursor)
                flow.addWidget(tag)
                if (i+1) % 5 == 0:
                    self.ml.addLayout(flow); flow = QHBoxLayout()
            self.ml.addLayout(flow)
        self.ml.addStretch()

    def add_mat(self):
        name, ok = QInputDialog.getText(self, "添加材料", "材料名称：")
        if ok and name.strip():
            t, ok2 = QInputDialog.getText(self, "添加材料", "类型（抗体/试剂/细胞系，可不填）：")
            if ok2:
                db.create_material(name.strip(), t.strip())
                self.load_data()


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(20,16,20,16)
        header = QHBoxLayout()
        title = QLabel("⚙️ 设置"); title.setStyleSheet("font-size:18px;font-weight:700;")
        header.addWidget(title); layout.addLayout(header)

        dc = QFrame(); dc.setStyleSheet("background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:16px;margin-top:12px;")
        dcl = QVBoxLayout(dc)
        dt = QLabel("数据存储"); dt.setStyleSheet("font-size:14px;font-weight:600;"); dcl.addWidget(dt)
        self.dbl = QLabel(); self.dbl.setStyleSheet("font-size:12px;color:#6b7085;font-family:monospace;"); self.dbl.setWordWrap(True); dcl.addWidget(self.dbl)
        sb = QPushButton("选择文件夹"); sb.setObjectName("btnSecondary"); sb.clicked.connect(self.sel_folder); dcl.addWidget(sb)
        hi = QLabel("建议将数据存储在云同步文件夹（如 OneDrive、iCloud）以实现自动备份。")
        hi.setStyleSheet("font-size:11px;color:#9ea2b5;"); hi.setWordWrap(True); dcl.addWidget(hi)
        layout.addWidget(dc)

        ac = QFrame(); ac.setStyleSheet("background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:16px;margin-top:12px;")
        acl = QVBoxLayout(ac)
        at = QLabel("关于 HelixDesk"); at.setStyleSheet("font-size:14px;font-weight:600;"); acl.addWidget(at)
        for k,v in [("版本","v2.0 (Python)"),("框架","PySide6 + SQLite"),("存储","本地 SQLite")]:
            r = QHBoxLayout(); r.addWidget(QLabel(k)); r.addStretch()
            vl = QLabel(v); vl.setStyleSheet("color:#6b7085;"); r.addWidget(vl); acl.addLayout(r)
        layout.addWidget(ac)

        sc = QFrame(); sc.setStyleSheet("background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:16px;margin-top:12px;")
        scl = QVBoxLayout(sc)
        st = QLabel("数据统计"); st.setStyleSheet("font-size:14px;font-weight:600;"); scl.addWidget(st)
        self.sv = {}
        for k in ["项目","实验","材料"]:
            r = QHBoxLayout(); r.addWidget(QLabel(k)); r.addStretch()
            vl = QLabel("加载中..."); vl.setStyleSheet("color:#6b7085;"); r.addWidget(vl); self.sv[k] = vl; scl.addLayout(r)
        layout.addWidget(sc); layout.addStretch()

    def load_data(self):
        cfg = db._cfg()
        p = cfg.get("dbPath", db.get_db_path())
        self.dbl.setText(f"当前位置：{p}")
        self.sv["项目"].setText(str(len(db.list_projects())))
        self.sv["实验"].setText(str(len(db.list_experiments())))
        self.sv["材料"].setText(str(len(db.list_materials())))

    def sel_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择数据库文件夹")
        if folder:
            np = os.path.join(folder, "helixdesk.db").replace("\\\\", "/")
            if db.migrate_db(np):
                QMessageBox.information(self, "成功", f"数据库已迁移到：{np}")
                self.load_data()
            else:
                QMessageBox.warning(self, "失败", "迁移失败，请检查目标路径是否可写。")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HelixDesk")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE)
        self.current_project_id = None

        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # Vara-style sidebar
        nav = QFrame(); nav.setObjectName("navPanel"); nav.setFixedWidth(200)
        nl = QVBoxLayout(nav); nl.setContentsMargins(0,0,0,0); nl.setSpacing(0)
        logo = QLabel("  🧬  HelixDesk")
        logo.setStyleSheet("font-size: 16px; font-weight: 700; color: #fff; padding: 16px 16px 12px;")
        nl.addWidget(logo)
        sep = QLabel(""); sep.setFixedHeight(1); sep.setStyleSheet("background: rgba(255,255,255,0.08); margin: 4px 12px;")
        nl.addWidget(sep)

        self.nav_btns = {}
        for key, icon, text in [("plan","📅","计划表"),("experiments","🧪","实验"),("materials","🧫","材料"),("settings","⚙️","设置")]:
            btn = QPushButton(f"   {icon}  {text}")
            btn.setCheckable(True); btn.setCursor(Qt.PointingHandCursor); btn.setFixedHeight(38)
            btn.clicked.connect(lambda checked, k=key: self.switch_view(k))
            nl.addWidget(btn); self.nav_btns[key] = btn

        nl.addSpacing(12)
        pt = QLabel("  📁 项目")
        pt.setStyleSheet("font-size: 11px; font-weight: 600; color: #8b8fa3; padding: 8px 16px 4px;")
        nl.addWidget(pt)
        self.project_list = QListWidget()
        self.project_list.setCursor(Qt.PointingHandCursor)
        self.project_list.itemClicked.connect(self.on_project_click)
        nl.addWidget(self.project_list, 1)
        npb = QPushButton("  + 新建项目")
        npb.setCursor(Qt.PointingHandCursor); npb.setFixedHeight(36)
        npb.setStyleSheet("QPushButton{text-align:left;padding:8px 16px;border:none;border-top:1px solid rgba(255,255,255,0.08);color:#8b8fa3;font-size:13px;}QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}")
        npb.clicked.connect(self.show_new_project)
        nl.addWidget(npb)
        ml.addWidget(nav)

        self.stack = QStackedWidget()
        self.cal_view = CalendarView(self)
        self.exp_view = ExperimentView(self)
        self.mat_view = MaterialView(self)
        self.set_view = SettingsView(self)
        for v in [self.cal_view, self.exp_view, self.mat_view, self.set_view]:
            self.stack.addWidget(v)
        ml.addWidget(self.stack, 1)

        self.load_projects()
        self.nav_btns["plan"].setChecked(True)

    def switch_view(self, key):
        for k, btn in self.nav_btns.items():
            btn.setChecked(k == key)
        idx = {"plan":0,"experiments":1,"materials":2,"settings":3}
        self.stack.setCurrentIndex(idx.get(key, 0))
        if key == "experiments": self.exp_view.load_data()
        elif key == "materials": self.mat_view.load_data()
        elif key == "settings": self.set_view.load_data()

    def load_projects(self):
        self.project_list.clear()
        item = QListWidgetItem("📂 所有实验")
        item.setData(Qt.UserRole, None)
        self.project_list.addItem(item)
        for p in db.list_projects():
            item = QListWidgetItem(f"📁 {p['name']}")
            item.setData(Qt.UserRole, p["id"])
            self.project_list.addItem(item)

    def on_project_click(self, item):
        self.current_project_id = item.data(Qt.UserRole)
        self.switch_view("experiments")

    def show_new_project(self):
        dlg = ProjectDialog(self)
        if dlg.exec():
            db.create_project(dlg.name_input.text().strip(), dlg.desc_input.toPlainText().strip())
            self.load_projects()
            if self.stack.currentIndex() == 1:
                self.exp_view.load_data()


def main():
    import sys
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    db.init()
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
