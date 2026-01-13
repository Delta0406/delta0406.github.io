---
title: extern关键字
date: 2025-05-24 16:02:16
tags: c++
categories: c++基础
---

# 前言
extern是一个修饰变量或函数的关键字，用于说明修饰的符号具有外部链接性。通过使用extern关键字，可以引用其他源文件中的变量和函数，实现模块化编程和代码重用。

# extern的用法
## 修饰变量
一般情况下，在一个源文件中定义的变量和函数只能被源文件中的函数调用，但是C++程序会有许多源文件，为了在本源文件中使用其他文件的变量，C++提供了extern关键字。在使用其他源文件中的全局变量时，只需要在本源文件中使用extern关键字来声明这个变量即可。示例如下：
```c++
// 在test1.cpp源文件中定义全局变量a、b、c
#include "test1.h"

int a = 1, b = 2;
char c = 'c';

// 在test1.h中声明变量a、b、c
#pragma once

extern int a, b;
extern char c;

//在test2.cpp源文件中要使用test1.cpp源文件中的全局变量a、b、c
#include <iostream>
#include "test1.h"
using namespace std;

int main() {
	cout << "a = " << a << endl;
	cout << "b = " << b << endl;
	cout << "c = " << c << endl;

	return 0;
}
```
编译器不会为`test2.cpp`源文件中的全局变量a、b、c分配内存空间，而是直接使用`test1.cpp`中的全局变量a、b、c。如果在`test2.cpp`中修改a、b、c的值，`test1.cpp`中变量的值也会发生改变。
> 在`test1.cpp`中`#include "test1.h"是为了防止声明与定义不一致，让编译器自动检查声明和定义的一致性。

## 修饰函数
与修饰变量类似，extern修饰函数，可以用于在一个文件中引用另一个文件中定义的函数。
```c++
// 文件1: main.cpp
extern void print_message();  // 声明一个外部函数

int main() {
    print_message();  // 调用外部函数
    return 0;
}

// 文件2: print.cpp
#include <iostream>

void print_message() {  // 定义一个函数
    std::cout << "Hello, World!" << std::endl;
}
```
在这个例子中，我们在 print.cpp 文件中定义了一个函数 print_message，然后在 main.cpp 文件中通过 extern 关键字声明了同名的外部函数 print_message，从而使其可以在 main.cpp 文件中调用。

## extern "C"
extern和"C"配合使用，可以解决C++代码和C代码之间的链接问题。

由于C++支持函数重载，所以在编译阶段，编译器会对函数名进行改编（mangling），以区分具有相同名字但参数类型不同的函数。然而，C 语言不支持函数重载，也就没有这个改编过程。因此，如果我们想在 C++ 代码中调用 C 代码，或者在 C 代码中调用 C++ 代码，就需要用到 extern "C"。
```c++
// 文件1: main.cpp (C++代码)
extern "C" void print_message();  // 使用 extern "C" 声明一个外部函数

int main() {
    print_message();  // 调用外部函数
    return 0;
}

// 文件2: print.c (C代码)
#include <stdio.h>

void print_message() {  // 定义一个函数
    printf("Hello, World!\n");
}
```
这个例子和前一个例子类似，但有一个重要的区别：print.c 是用 C 语言编写的，而 main.cpp 是用 C++ 编写的。因此，我们需要用 extern "C" 来声明 print_message 函数，以确保 C++ 编译器能正确链接到 C 语言编写的 print_message 函数。

# 参考
[深入理解 C++ 中的 extern 关键字](https://www.51cto.com/article/768503.html)