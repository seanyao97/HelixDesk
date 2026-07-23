import sys
import os
from datetime import datetime, date, timedelta
from calendar import monthcalendar
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame, QScrollArea, QGridLayout, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog,
    QSplitter, QInputDialog
)
from PySide6.QtCore import Qt, QDate, Signal
from helixdesk import database as db

STYLE = '''
QMainWindow { background: #f5f6fa; }
QWidget { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 13px; color: #1a1d2e; }
#navPanel { background: #1a1d2e; min-width: 180px; max-width: 180px; }
#navPanel QPushButton { text-align: left; padding: 10px 16px; border: none; border-radius: 6px; color: #8b8fa3; font-size: 13px; margin: 2px 8px; }
#navPanel QPushButton:hover { background: #25283d; color: #fff; }
#navPanel QPushButton:checked { background: #2d3150; color: #fff; font-weight: 600; }
#navTitle { color: #8b8fa3; font-size: 11px; font-weight: 600; padding: 16px 16px 4px; text-transform: uppercase; letter-spacing: 1px; }
QPushButton#btnPrimary { background: #4f6ef7; color: #fff; border: none; border-radius: 6px; padding: 7px 18px; font-weight: 500; }
QPushButton#btnPrimary:hover { background: #3b56d9; }
QPushButton#btnSecondary { background: #f5f6fa; color: #1a1d2e; border: 1px solid #e8eaf0; border-radius: 6px; padding: 6px 14px; }
QPushButton#btnSecondary:hover { border-color: #4f6ef7; color: #4f6ef7; }
QPushButton#btnDanger { background: none; color: #ef4444; border: none; padding: 4px 10px; border-radius: 4px; }
QPushButton#btnDanger:hover { background: #fef2f2; }
QLineEdit, QTextEdit, QComboBox { border: 1px solid #e8eaf0; border-radius: 6px; padding: 7px 10px; background: #fff; }
QLineEdit:focus, QTextEdit:focus { border-color: #4f6ef7; }
QListWidget { border: none; background: transparent; }
QListWidget::item { padding: 8px 12px; border-radius: 6px; }
QListWidget::item:hover { background: #f0f4ff; }
QListWidget::item:selected { background: #eef1ff; color: #4f6ef7; }
QScrollBar:vertical { width: 5px; background: transparent; }
QScrollBar::handle:vertical { background: #d0d3dc; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #b0b3be; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
'''

def status_label(s):
    return {'draft': '草稿', 'submitted': '已提交', 'archived': '已归档'}.get(s, s)

def today_str():
    return datetime.now().strftime('%Y-%m-%d')


class ProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建项目')
        self.setMinimumWidth(380)
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('项目名称')
        layout.addRow('名称 *', self.name_input)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText('项目描述（可选）')
        self.desc_input.setMaximumHeight(80)
        layout.addRow('描述', self.desc_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
        self.name_input.setFocus()


class ExperimentDialog(QDialog):
    def __init__(self, parent=None, experiment=None):
        super().__init__(parent)
        self.experiment = experiment
        self.setWindowTitle('编辑实验' if experiment else '新建实验')
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText('实验标题')
        layout.addRow('标题 *', self.title_input)
        self.purpose_input = QTextEdit()
        self.purpose_input.setPlaceholderText('实验目的')
        self.purpose_input.setMaximumHeight(60)
        layout.addRow('目的', self.purpose_input)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addRow('日期', self.date_input)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText('实验室/房间')
        layout.addRow('地点', self.location_input)
        self.project_combo = QComboBox()
        for p in db.list_projects():
            self.project_combo.addItem(p['name'], p['id'])
        layout.addRow('所属项目', self.project_combo)
        if experiment:
            self.title_input.setText(experiment.get('title', ''))
            self.purpose_input.setPlainText(experiment.get('purpose', ''))
            if experiment.get('date'):
                self.date_input.setDate(QDate.fromString(experiment['date'], 'yyyy-MM-dd'))
            self.location_input.setText(experiment.get('location', ''))
            idx = self.project_combo.findData(experiment.get('project_id'))
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
        self.title_input.setFocus()

    def accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, '提示', '请输入实验标题')
            return
        super().accept()


class StepDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加步骤')
        self.setMinimumWidth(380)
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText('步骤标题')
        layout.addRow('标题 *', self.title_input)
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText('操作细节、注意事项')
        self.content_input.setMaximumHeight(100)
        layout.addRow('说明', self.content_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
        self.title_input.setFocus()

    def accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, '提示', '请输入步骤标题')
            return
        super().accept()

class CalendarView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        nav = QHBoxLayout()
        title = QLabel('📅 计划表')
        title.setStyleSheet('font-size: 18px; font-weight: 700;')
        nav.addWidget(title)
        nav.addStretch()
        self.month_label = QLabel()
        self.month_label.setStyleSheet('font-size: 16px; font-weight: 600; min-width: 140px;')
        nav.addWidget(self.month_label)
        prev_btn = QPushButton('‹')
        prev_btn.setFixedSize(32, 32)
        prev_btn.clicked.connect(lambda: self.navigate(-1))
        nav.addWidget(prev_btn)
        next_btn = QPushButton('›')
        next_btn.setFixedSize(32, 32)
        next_btn.clicked.connect(lambda: self.navigate(1))
        nav.addWidget(next_btn)
        today_btn = QPushButton('今天')
        today_btn.setObjectName('btnSecondary')
        today_btn.clicked.connect(self.go_today)
        nav.addWidget(today_btn)
        layout.addLayout(nav)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.cal_widget = QWidget()
        self.cal_grid = QGridLayout(self.cal_widget)
        self.cal_grid.setSpacing(1)
        scroll.setWidget(self.cal_widget)
        layout.addWidget(scroll, 1)
        self.render()

    def navigate(self, delta):
        self.current_month += delta
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        elif self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.render()

    def go_today(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.render()

    def render(self):
        while self.cal_grid.count():
            item = self.cal_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        months = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']
        self.month_label.setText(f'{self.current_year}年 {months[self.current_month-1]}')
        for i, d in enumerate(['日','一','二','三','四','五','六']):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #9ea2b5; padding: 6px;')
            self.cal_grid.addWidget(lbl, 0, i)
        month_str = f'{self.current_year}-{self.current_month:02d}'
        all_exps = db.list_experiments()
        all_plans = db.list_plans()
        day_data = {}
        cal = monthcalendar(self.current_year, self.current_month)
        for week in cal:
            for d in week:
                if d:
                    ds = f'{month_str}-{d:02d}'
                    day_data[ds] = {'exps': [], 'todos': [], 'dones': []}
        for e in all_exps:
            if e['date'] and e['date'] in day_data:
                day_data[e['date']]['exps'].append(e)
        for p in all_plans:
            if p['date'] and p['date'] in day_data:
                if p['done']: day_data[p['date']]['dones'].append(p)
                else: day_data[p['date']]['todos'].append(p)
        today = today_str()
        for wi, week in enumerate(cal):
            for di, d in enumerate(week):
                if d == 0:
                    cell = QLabel()
                    cell.setStyleSheet('background: #fafbfc;')
                    self.cal_grid.addWidget(cell, wi+1, di)
                    continue
                ds = f'{month_str}-{d:02d}'
                data = day_data.get(ds, {'exps':[],'todos':[],'dones':[]})
                cell = QWidget()
                cell.setStyleSheet('background: #fff;' if ds != today else 'background: #eef1ff;')
                cl = QVBoxLayout(cell)
                cl.setContentsMargins(4,2,4,2)
                cl.setSpacing(1)
                num = QLabel(str(d))
                num.setStyleSheet('font-size:12px;font-weight:600;padding:2px 0;')
                if ds == today:
                    num.setStyleSheet('font-size:12px;font-weight:700;color:#4f6ef7;padding:2px 0;')
                cl.addWidget(num)
                for e in data['exps']:
                    lbl = QLabel(e['title'][:10]+('...' if len(e['title'])>10 else ''))
                    lbl.setStyleSheet('background:#eef1ff;color:#4f6ef7;padding:1px 4px;border-radius:3px;font-size:10px;')
                    cl.addWidget(lbl)
                for p in data['todos']:
                    lbl = QLabel(p['title'][:10]+('...' if len(p['title'])>10 else ''))
                    lbl.setStyleSheet('background:#fffbeb;color:#f59e0b;padding:1px 4px;border-radius:3px;font-size:10px;')
                    cl.addWidget(lbl)
                for p in data['dones']:
                    lbl = QLabel('✓ '+p['title'][:8])
                    lbl.setStyleSheet('background:#ecfdf5;color:#22c55e;padding:1px 4px;border-radius:3px;font-size:10px;')
                    cl.addWidget(lbl)
                cl.addStretch()
                cell.setCursor(Qt.PointingHandCursor)
                cell.mousePressEvent = lambda e, ds=ds: self.on_day_click(ds)
                self.cal_grid.addWidget(cell, wi+1, di)

    def on_day_click(self, date_str):
        title, ok = QInputDialog.getText(self, '添加事项', f'在 {date_str} 添加：')
        if ok and title.strip():
            db.add_plan(date_str, title.strip())
            self.render()

class ExperimentCard(QFrame):
    clicked = Signal()
    def __init__(self, exp, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('ExperimentCard{background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:14px;}ExperimentCard:hover{border-color:#4f6ef7;}')
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14,12,14,12)
        layout.setSpacing(4)
        title = QLabel(exp['title'])
        title.setStyleSheet('font-size:14px;font-weight:600;')
        layout.addWidget(title)
        meta = QLabel(f'{exp["date"] or ""}  ·  {exp.get("project_name","")}')
        meta.setStyleSheet('font-size:12px;color:#6b7085;')
        layout.addWidget(meta)
        if exp.get('purpose'):
            p = QLabel(exp['purpose'])
            p.setStyleSheet('font-size:12px;color:#9ea2b5;')
            p.setWordWrap(True)
            p.setMaximumHeight(36)
            layout.addWidget(p)
        s = exp['status']
        colors = {'draft':('#eef1ff','#4f6ef7'),'submitted':('#fffbeb','#f59e0b'),'archived':('#ecfdf5','#22c55e')}
        bg, fg = colors.get(s,('#eef1ff','#4f6ef7'))
        status = QLabel(status_label(s))
        status.setStyleSheet(f'background:{bg};color:{fg};padding:1px 8px;border-radius:8px;font-size:11px;')
        status.setFixedWidth(60)
        layout.addWidget(status)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class StepWidget(QFrame):
    deleted = Signal()
    def __init__(self, step, index, parent=None):
        super().__init__(parent)
        self.setStyleSheet('StepWidget{background:#fff;border:1px solid #e8eaf0;border-radius:8px;padding:10px;margin:4px 0;}')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12,10,12,10)
        header = QHBoxLayout()
        num = QLabel(f'{index}. {step["title"]}')
        num.setStyleSheet('font-weight:600;font-size:13px;')
        header.addWidget(num)
        header.addStretch()
        del_btn = QPushButton('删除')
        del_btn.setObjectName('btnDanger')
        del_btn.clicked.connect(self.deleted.emit)
        header.addWidget(del_btn)
        layout.addLayout(header)
        if step.get('content'):
            c = QLabel(step['content'])
            c.setStyleSheet('font-size:12px;color:#6b7085;')
            c.setWordWrap(True)
            layout.addWidget(c)


class ResultWidget(QFrame):
    deleted = Signal()
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.setStyleSheet('ResultWidget{background:#fafbfc;border:1px dashed #e8eaf0;border-radius:6px;padding:8px;margin:2px 0;}')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10,6,10,6)
        text = QLabel(result['content'])
        text.setWordWrap(True)
        text.setStyleSheet('font-size:12px;')
        layout.addWidget(text, 1)
        del_btn = QPushButton('✕')
        del_btn.setFixedSize(20,20)
        del_btn.setStyleSheet('border:none;color:#9ea2b5;font-size:12px;')
        del_btn.clicked.connect(self.deleted.emit)
        layout.addWidget(del_btn)

class ExperimentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,16,20,16)
        header = QHBoxLayout()
        title = QLabel('🧪 实验')
        title.setStyleSheet('font-size:18px;font-weight:700;')
        header.addWidget(title)
        header.addStretch()
        self.new_exp_btn = QPushButton('+ 新建实验')
        self.new_exp_btn.setObjectName('btnPrimary')
        self.new_exp_btn.clicked.connect(self.show_new_experiment)
        header.addWidget(self.new_exp_btn)
        self.new_proj_btn = QPushButton('+ 新建项目')
        self.new_proj_btn.setObjectName('btnSecondary')
        self.new_proj_btn.clicked.connect(self.show_new_project)
        header.addWidget(self.new_proj_btn)
        layout.addLayout(header)
        self.filter_layout = QHBoxLayout()
        layout.addLayout(self.filter_layout)
        splitter = QSplitter(Qt.Horizontal)
        list_widget = QWidget()
        list_lo = QVBoxLayout(list_widget)
        list_lo.setContentsMargins(0,0,0,0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.exp_container = QWidget()
        self.exp_list_layout = QVBoxLayout(self.exp_container)
        self.exp_list_layout.setSpacing(8)
        self.exp_list_layout.addStretch()
        scroll.setWidget(self.exp_container)
        list_lo.addWidget(scroll)
        splitter.addWidget(list_widget)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(16,0,0,0)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.NoFrame)
        self.detail_content = QWidget()
        self.detail_inner = QVBoxLayout(self.detail_content)
        self.detail_scroll.setWidget(self.detail_content)
        self.detail_layout.addWidget(self.detail_scroll)
        splitter.addWidget(self.detail_widget)
        splitter.setSizes([400,500])
        layout.addWidget(splitter, 1)
        self.filter_btns = []

    def load_data(self):
        self.load_filters()
        self.load_experiments()

    def load_filters(self):
        for btn in self.filter_btns:
            self.filter_layout.removeWidget(btn)
            btn.deleteLater()
        self.filter_btns.clear()
        win = self.window()
        pid = win.current_project_id if hasattr(win,'current_project_id') else None
        btn = QPushButton('全部')
        btn.setCheckable(True)
        btn.setChecked(pid is None)
        btn.clicked.connect(lambda: self.filter_by(None))
        self.filter_layout.addWidget(btn)
        self.filter_btns.append(btn)
        for p in db.list_projects():
            btn = QPushButton(p['name'])
            btn.setCheckable(True)
            btn.setChecked(p['id'] == pid)
            btn.clicked.connect(lambda checked, x=p['id']: self.filter_by(x))
            self.filter_layout.addWidget(btn)
            self.filter_btns.append(btn)
        self.filter_layout.addStretch()

    def filter_by(self, pid):
        win = self.window()
        win.current_project_id = pid
        for b in self.filter_btns:
            b.setChecked(False)
        self.sender().setChecked(True)
        self.load_experiments()

    def load_experiments(self):
        while self.exp_list_layout.count():
            item = self.exp_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        win = self.window()
        pid = win.current_project_id if hasattr(win,'current_project_id') else None
        exps = db.list_experiments(pid)
        for e in exps:
            card = ExperimentCard(e, self)
            card.clicked.connect(lambda x=e['id']: self.show_detail(x))
            self.exp_list_layout.addWidget(card)
        self.exp_list_layout.addStretch()
        if not exps:
            lbl = QLabel('暂无实验记录')
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet('color:#9ea2b5;padding:40px;')
            self.exp_list_layout.addWidget(lbl)

    def show_detail(self, eid):
        exp = db.get_experiment(eid)
        if not exp: return
        while self.detail_inner.count():
            item = self.detail_inner.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        title = QLabel(exp['title'])
        title.setStyleSheet('font-size:18px;font-weight:700;')
        self.detail_inner.addWidget(title)
        meta = QLabel(f'📅 {exp["date"] or ""}  📍 {exp["location"] or "未指定"}  [{status_label(exp["status"])}]')
        meta.setStyleSheet('color:#6b7085;font-size:12px;')
        self.detail_inner.addWidget(meta)
        if exp['purpose']:
            pu = QLabel(exp['purpose'])
            pu.setStyleSheet('background:#eef1ff;padding:10px 14px;border-radius:6px;border-left:3px solid #4f6ef7;')
            pu.setWordWrap(True)
            self.detail_inner.addWidget(pu)
        # Steps
        st = QLabel(f'📋 步骤 ({len(exp["steps"])})')
        st.setStyleSheet('font-size:14px;font-weight:600;margin-top:12px;')
        self.detail_inner.addWidget(st)
        asbtn = QPushButton('+ 添加步骤')
        asbtn.setObjectName('btnSecondary')
        asbtn.clicked.connect(lambda: self.add_step(eid))
        self.detail_inner.addWidget(asbtn)
        if exp['steps']:
            for i, s in enumerate(exp['steps']):
                sw = StepWidget(s, i+1)
                sw.deleted.connect(lambda x=s['id']: (db.delete_step(x), self.show_detail(eid)))
                self.detail_inner.addWidget(sw)
        else:
            self.detail_inner.addWidget(QLabel('暂无步骤'))
        # Results
        rt = QLabel(f'📊 结果 ({len(exp["results"])})')
        rt.setStyleSheet('font-size:14px;font-weight:600;margin-top:12px;')
        self.detail_inner.addWidget(rt)
        arbtn = QPushButton('+ 记录结果')
        arbtn.setObjectName('btnSecondary')
        arbtn.clicked.connect(lambda: self.add_result(eid))
        self.detail_inner.addWidget(arbtn)
        for r in exp['results']:
            rw = ResultWidget(r)
            rw.deleted.connect(lambda x=r['id']: (db.delete_result(x), self.show_detail(eid)))
            self.detail_inner.addWidget(rw)
        # Actions
        act = QHBoxLayout()
        edit_btn = QPushButton('✏️ 编辑')
        edit_btn.setObjectName('btnSecondary')
        edit_btn.clicked.connect(lambda: self.edit_exp(eid))
        act.addWidget(edit_btn)
        sc = QComboBox()
        sc.addItems(['草稿','已提交','已归档'])
        sm = {'草稿':'draft','已提交':'submitted','已归档':'archived'}
        sc.setCurrentText([k for k,v in sm.items() if v==exp['status']][0])
        sc.currentTextChanged.connect(lambda t: db.update_experiment(eid,{'status':sm[t]}))
        act.addWidget(sc)
        apbtn = QPushButton('📋 加入计划')
        apbtn.setObjectName('btnSecondary')
        apbtn.clicked.connect(lambda: (db.add_plan(today_str(), exp['title'], eid), QMessageBox.information(self,'提示','已加入今日计划')))
        act.addWidget(apbtn)
        self.detail_inner.addLayout(act)
        self.detail_inner.addStretch()
        # 清除旧详情，加载新的
        while self.detail_inner.count():
            pass

    def show_new_project(self):
        dlg = ProjectDialog(self)
        if dlg.exec():
            db.create_project(dlg.name_input.text().strip(), dlg.desc_input.toPlainText().strip())
            self.load_data()

    def show_new_experiment(self):
        dlg = ExperimentDialog(self)
        if dlg.exec():
            db.create_experiment(dlg.project_combo.currentData(), dlg.title_input.text().strip(),
                dlg.purpose_input.toPlainText().strip(), dlg.date_input.date().toString('yyyy-MM-dd'),
                dlg.location_input.text().strip())
            self.load_data()

    def edit_exp(self, eid):
        exp = db.get_experiment(eid)
        if not exp: return
        dlg = ExperimentDialog(self, exp)
        if dlg.exec():
            db.update_experiment(eid,{'title':dlg.title_input.text().strip(),
                'purpose':dlg.purpose_input.toPlainText().strip(),
                'date':dlg.date_input.date().toString('yyyy-MM-dd'),
                'location':dlg.location_input.text().strip()})
            self.show_detail(eid)
            self.load_experiments()

    def add_step(self, eid):
        dlg = StepDialog(self)
        if dlg.exec():
            db.add_step(eid, dlg.title_input.text().strip(), dlg.content_input.toPlainText().strip())
            self.show_detail(eid)

    def add_result(self, eid):
        content, ok = QInputDialog.getMultiLineText(self, '记录结果', '输入结果内容：')
        if ok and content.strip():
            db.add_result(eid, content.strip())
            self.show_detail(eid)

class MaterialView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,16,20,16)
        header = QHBoxLayout()
        title = QLabel('🧫 材料库')
        title.setStyleSheet('font-size:18px;font-weight:700;')
        header.addWidget(title)
        header.addStretch()
        self.add_btn = QPushButton('+ 添加材料')
        self.add_btn.setObjectName('btnPrimary')
        self.add_btn.clicked.connect(self.add_material)
        header.addWidget(self.add_btn)
        layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.mat_container = QWidget()
        self.mat_layout = QVBoxLayout(self.mat_container)
        scroll.setWidget(self.mat_container)
        layout.addWidget(scroll, 1)

    def load_data(self):
        while self.mat_layout.count():
            item = self.mat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        mats = db.list_materials()
        if not mats:
            lbl = QLabel('材料库为空')
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet('color:#9ea2b5;padding:40px;')
            self.mat_layout.addWidget(lbl)
        else:
            flow = QHBoxLayout()
            flow.setSpacing(6)
            for i, m in enumerate(mats):
                tag = QPushButton(m['name'])
                tag.setStyleSheet('QPushButton{background:#eef1ff;color:#4f6ef7;border:none;border-radius:14px;padding:5px 14px;font-size:13px;font-weight:500;}QPushButton:hover{background:#dce3ff;}')
                tag.setCursor(Qt.PointingHandCursor)
                flow.addWidget(tag)
                if (i+1) % 5 == 0:
                    self.mat_layout.addLayout(flow)
                    flow = QHBoxLayout()
            self.mat_layout.addLayout(flow)
        self.mat_layout.addStretch()

    def add_material(self):
        name, ok = QInputDialog.getText(self, '添加材料', '材料名称：')
        if ok and name.strip():
            t, ok2 = QInputDialog.getText(self, '添加材料', '类型（抗体/试剂/细胞系，可不填）：')
            if ok2:
                db.create_material(name.strip(), t.strip())
                self.load_data()


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,16,20,16)
        header = QHBoxLayout()
        title = QLabel('⚙️ 设置')
        title.setStyleSheet('font-size:18px;font-weight:700;')
        header.addWidget(title)
        layout.addLayout(header)
        # Data storage card
        dc = QFrame()
        dc.setStyleSheet('background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:16px;margin-top:12px;')
        dcl = QVBoxLayout(dc)
        db_title = QLabel('数据存储')
        db_title.setStyleSheet('font-size:14px;font-weight:600;')
        dcl.addWidget(db_title)
        self.db_label = QLabel()
        self.db_label.setStyleSheet('font-size:12px;color:#6b7085;font-family:monospace;')
        self.db_label.setWordWrap(True)
        dcl.addWidget(self.db_label)
        sel_btn = QPushButton('选择文件夹')
        sel_btn.setObjectName('btnSecondary')
        sel_btn.clicked.connect(self.select_folder)
        dcl.addWidget(sel_btn)
        hint = QLabel('建议将数据存储在云同步文件夹（如 OneDrive、iCloud）以实现自动备份。')
        hint.setStyleSheet('font-size:11px;color:#9ea2b5;')
        hint.setWordWrap(True)
        dcl.addWidget(hint)
        layout.addWidget(dc)
        # About card
        ac = QFrame()
        ac.setStyleSheet('background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:16px;margin-top:12px;')
        acl = QVBoxLayout(ac)
        acl_title = QLabel('关于 HelixDesk')
        acl_title.setStyleSheet('font-size:14px;font-weight:600;')
        acl.addWidget(acl_title)
        for k,v in [('版本','v2.0 (Python)'),('框架','PySide6 + SQLite'),('存储','本地 SQLite')]:
            r = QHBoxLayout()
            r.addWidget(QLabel(k))
            r.addStretch()
            vl = QLabel(v)
            vl.setStyleSheet('color:#6b7085;')
            r.addWidget(vl)
            acl.addLayout(r)
        layout.addWidget(ac)
        # Stats card
        sc2 = QFrame()
        sc2.setStyleSheet('background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:16px;margin-top:12px;')
        scl = QVBoxLayout(sc2)
        scl_title = QLabel('数据统计')
        scl_title.setStyleSheet('font-size:14px;font-weight:600;')
        scl.addWidget(scl_title)
        self.stat_vals = {}
        for k in ['项目','实验','材料']:
            r = QHBoxLayout()
            r.addWidget(QLabel(k))
            r.addStretch()
            vl = QLabel('加载中...')
            vl.setStyleSheet('color:#6b7085;')
            r.addWidget(vl)
            self.stat_vals[k] = vl
            scl.addLayout(r)
        layout.addWidget(sc2)
        layout.addStretch()

    def load_data(self):
        config = db.load_config()
        p = config.get('dbPath', db.get_default_db_path())
        self.db_label.setText(f'当前位置：{p}')
        self.stat_vals['项目'].setText(str(len(db.list_projects())))
        self.stat_vals['实验'].setText(str(len(db.list_experiments())))
        self.stat_vals['材料'].setText(str(len(db.list_materials())))

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择数据库文件夹')
        if folder:
            new_path = os.path.join(folder, 'helixdesk.db').replace('\\', '/')
            if db.migrate_db(new_path):
                QMessageBox.information(self, '成功', f'数据库已迁移到：{new_path}')
                self.load_data()
            else:
                QMessageBox.warning(self, '失败', '迁移失败，请检查目标路径是否可写。')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('HelixDesk')
        self.resize(1200, 780)
        self.setStyleSheet(STYLE)
        self.current_project_id = None

        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(0,0,0,0)
        ml.setSpacing(0)

        # Nav
        nav = QFrame()
        nav.setObjectName('navPanel')
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(0,0,0,0)
        nl.setSpacing(0)
        nt = QLabel('项目导航')
        nt.setObjectName('navTitle')
        nl.addWidget(nt)
        self.nav_btns = {}
        for key, icon, text in [('plan','📋','计划表'),('experiments','🧪','实验'),('materials','🧫','材料'),('settings','⚙️','设置')]:
            btn = QPushButton(f'{icon}  {text}')
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.switch_view(k))
            nl.addWidget(btn)
            self.nav_btns[key] = btn
        nl.addStretch()
        pt = QLabel('项目列表')
        pt.setObjectName('navTitle')
        nl.addWidget(pt)
        self.project_list = QListWidget()
        self.project_list.setCursor(Qt.PointingHandCursor)
        self.project_list.itemClicked.connect(self.on_project_click)
        nl.addWidget(self.project_list)
        npb = QPushButton('+ 新建项目')
        npb.setCursor(Qt.PointingHandCursor)
        npb.clicked.connect(self.show_new_project)
        nl.addWidget(npb)
        ml.addWidget(nav)

        # Stack
        self.stack = QStackedWidget()
        self.cal_view = CalendarView(self)
        self.exp_view = ExperimentView(self)
        self.mat_view = MaterialView(self)
        self.set_view = SettingsView(self)
        self.stack.addWidget(self.cal_view)
        self.stack.addWidget(self.exp_view)
        self.stack.addWidget(self.mat_view)
        self.stack.addWidget(self.set_view)
        ml.addWidget(self.stack, 1)

        self.load_projects()
        self.nav_btns['plan'].setChecked(True)

    def switch_view(self, key):
        for k, btn in self.nav_btns.items():
            btn.setChecked(k == key)
        idx = {'plan':0,'experiments':1,'materials':2,'settings':3}
        self.stack.setCurrentIndex(idx.get(key,0))
        if key == 'experiments': self.exp_view.load_data()
        elif key == 'materials': self.mat_view.load_data()
        elif key == 'settings': self.set_view.load_data()

    def load_projects(self):
        self.project_list.clear()
        item = QListWidgetItem('📂 所有实验')
        item.setData(Qt.UserRole, None)
        self.project_list.addItem(item)
        for p in db.list_projects():
            item = QListWidgetItem(f'📁 {p["name"]}')
            item.setData(Qt.UserRole, p['id'])
            self.project_list.addItem(item)

    def on_project_click(self, item):
        self.current_project_id = item.data(Qt.UserRole)
        self.switch_view('experiments')

    def show_new_project(self):
        dlg = ProjectDialog(self)
        if dlg.exec():
            db.create_project(dlg.name_input.text().strip(), dlg.desc_input.toPlainText().strip())
            self.load_projects()


def main():
    import sys
    os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')
    os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    db.init_db()
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
