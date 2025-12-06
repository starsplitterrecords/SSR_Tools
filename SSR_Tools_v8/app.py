import tkinter as tk
from gui.main_view import MainWindow

def main():
    root = tk.Tk()
    root.title("SSR Tools v8")
    root.geometry("1400x900")
    root.minsize(1100, 700)

    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
