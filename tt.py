# from pywinauto import Desktop
# from pywinauto.keyboard import send_keys

# # вариант 1: адресно по окну Save As
# dlg = Desktop(backend="uia").window(title_re=".*Сохранить как.*")
# if dlg.exists(timeout=2):
#     dlg.set_focus()
#     dlg.type_keys("{ESC}")

# # вариант 2: глобально (если заголовок нестабилен)
# # send_keys("{ESC}")

from pywinauto import Desktop
from pywinauto.keyboard import send_keys

dlg = Desktop(backend="win32").window(class_name="#32770", title_re=r"^(Сохранить как|Save As)$")
if dlg.exists(timeout=3):
    dlg.set_focus()

    # Надежнее сначала нажать "Отмена"/"Cancel"
    cancel = dlg.child_window(title_re=r"^(Отмена|Cancel)$", class_name="Button")
    if cancel.exists(timeout=1):
        cancel.click_input()
    else:
        dlg.type_keys("{ESC}")   # fallback
else:
    send_keys("{ESC}")           # fallback в активное окно
