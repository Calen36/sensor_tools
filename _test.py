import tkinter as tk

def copy_text(event):
    widget = event.widget
    selected_text = widget.selection_get()
    root.clipboard_clear()
    root.clipboard_append(selected_text)

def paste_text(event):
    widget = event.widget
    text = root.clipboard_get()
    widget.insert('insert', text)

root = tk.Tk()

entry = tk.Entry(root)
entry.pack()

entry.bind('<Control-c>', copy_text)
entry.bind('<Control-v>', paste_text)

root.mainloop()