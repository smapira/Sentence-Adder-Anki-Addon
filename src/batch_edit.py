# -*- coding: utf-8 -*-
##############################################
##                                          ##
##              Sentence Adder              ##
##                  v1.0.5                  ##
##                                          ##
##          Copyright (c) Mani 2021         ##
##      (https://github.com/krmanik)        ##
##                                          ##
##############################################

from aqt.qt import *
from aqt.utils import tooltip

from anki.hooks import addHook

from .editor import getRandomSentence, config_data

from datetime import datetime

folder = os.path.dirname(__file__)


class GetSentenceThread(QThread):
    finish = pyqtSignal(int)

    def __init__(self, mw1, nids, wordField, senField):
        QThread.__init__(self)
        self.mw1 = mw1
        self.nids = nids
        self.wordField = wordField
        self.senField = senField

    def run(self):
        count = 0
        tstamp = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        out = open(folder + "/user_files/not_found_" + tstamp + ".txt", "w", encoding="utf-8")

        for nid in self.nids:
            note = self.mw1.col.get_note(nid)
            if self.wordField in note:
                word = note[self.wordField]
                randomSen = getRandomSentence(word)
                print(randomSen)

                if randomSen != None:
                    if config_data['word_color']:
                        tmp_word = '<font color="' + config_data['word_color'] + '">' + word + "</font>"
                    else:
                        tmp_word = word

                    # wrap word in html
                    if config_data['word_html']:
                        word_html = config_data['word_html'].split("{{word}}")
                        if len(word_html) == 2 and word_html[0] and word_html[1]:
                            tmp_word = word_html[0] + word + word_html[1]

                    # wrap sentence in html
                    sen_html = ["", ""]
                    if config_data['sen_html']:
                        sen_html = config_data['sen_html'].split("{{sentence}}")

                    for sen in randomSen:
                        sen = sen[0].replace(word, tmp_word)

                        if len(sen_html) == 2 and sen_html[0] and sen_html[1]:
                            sen = sen_html[0] + sen + sen_html[1]

                        if config_data['text_color']:
                            note[self.senField] += '<font color="' + config_data['text_color'] + '">' + sen + "</font>"
                        else:
                            note[self.senField] += sen

                        note[self.senField] += "<br>"
                    count += 1
                else:
                    tooltip("Sentence not found for " + word)
                    out.write(word + "\n")
                note.flush()
        self.finish.emit(count)


class SentenceBatchEdit(QDialog):
    def __init__(self, browser, nids):
        QDialog.__init__(self, parent=browser)
        self.setWindowTitle("Sentence Batch Adder")
        self.browser = browser
        self.nids = nids

        self.resize(400, 300)

        layout = QVBoxLayout()

        topLayout = QFormLayout()

        self.selectFieldsComboBox = QComboBox()
        self.wordsComboBox = QComboBox()

        nid = self.nids[0]
        self.mw = self.browser.mw
        note_type = self.mw.col.get_note(nid).note_type()
        fields = self.mw.col.models.field_names(note_type)

        self.selectFieldsComboBox.addItems(fields)
        self.selectFieldsComboBox.setCurrentText(fields[0])

        self.wordsComboBox.addItems(fields)
        self.wordsComboBox.setCurrentText(fields[0])

        self.auto_add_rb = QRadioButton("Auto Add")
        self.all_sen_win_rb = QRadioButton("Open All Sentences Window")


        topLayout.addRow(QLabel("<b>Select fields and start batch add</b>"))

        topLayout.addRow(QLabel("Select words field"), self.wordsComboBox)
        topLayout.addRow(QLabel("Select sentence field"), self.selectFieldsComboBox)

        # topLayout.addRow(self.auto_add_rb)
        # topLayout.addRow(self.all_sen_win_rb)

        buttonBoxLayout = QHBoxLayout()

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.addButton("Start", QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonBox.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)

        self.buttonBox.accepted.connect(self.startBatchAdder)
        self.buttonBox.rejected.connect(self.close)

        buttonBoxLayout.addWidget(self.buttonBox)

        layout.addLayout(topLayout)
        layout.addLayout(buttonBoxLayout)
        self.setLayout(layout)
        self.get_sen_thread = None

    def startBatchAdder(self):
        mw = self.browser.mw
        mw.checkpoint("batch edit")
        mw.progress.start()
        self.browser.model.beginReset()

        wordField = self.wordsComboBox.currentText()
        senField = self.selectFieldsComboBox.currentText()
        self.get_sen_thread = GetSentenceThread(self.browser.mw, self.nids, wordField, senField)
        self.get_sen_thread.finish.connect(self.finished)
        self.get_sen_thread.start()

    def finished(self, result):
        mw = self.browser.mw
        self.browser.model.endReset()
        mw.progress.finish()
        mw.reset()
        tooltip("<b>Updated</b> {0} notes.".format(result), parent=self.browser)


def onSentenceBatchEdit(browser):
    nids = browser.selectedNotes()
    if not nids:
        tooltip("No cards selected.")
        return
    dlg = SentenceBatchEdit(browser, nids)
    dlg.exec()


def addMenu(browser):
    menu = browser.form.menuEdit
    menu.addSeparator()
    action = menu.addAction('Sentence Batch Adder...')
    action.triggered.connect(lambda x, b=browser: onSentenceBatchEdit(b))


addHook("browser.setupMenus", addMenu)
