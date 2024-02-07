class PrintLogger(object):  # создаем file like object
    """ Логгер для перенаправления stdout в текстовый виджет """
    def __init__(self, textbox):  # передаем текстовый виджет
        self.textbox = textbox 

    def write(self, text):
        self.textbox.configure(state="normal")  # делаем поле редактируемым
        self.textbox.insert("end", text)  # добавляем текст
        self.textbox.see("end")  # скроллим в конец
        self.textbox.configure(state="disabled")  # делаем поле не-редактируемым

    def flush(self):  # метод необходим для file like объектов
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
