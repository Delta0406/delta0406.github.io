---
title: const关键字
date: 2025-05-26 10:34:05
tags: c++
categories: c++基础
---

# 前言
`const`是C++中用于指示变量值不可变（常量）的关键字，被`const`修饰的变量在编译时会被视为只读，尝试修改其值会导致编译错误。通过使用`const`可以提高代码的安全性与可读性。

# `const`用于变量声明
`const`关键字通常放在变量类型前面，例如：
```c++
const int a = 10;
```
不过放在变量类型后面也是可以的：
```c++
int const a = 10;
```
可以使用变量初始化常量，也可以将常量赋值给变量：
```c++
int i1 = 10;
const int i2 = i1;
int i3 = i2;
```
`const`修饰的变量必须初始化：
```c++
const int i4; // 错误，const修饰的变量必须初始化
```

# 编译器对`const`修饰变量的处理
编译器在编译过程中会将用到`const`修饰变量的地方替换成对应的值，因此编译器必须知道变量的初始值。但是编译阶段各文件是独立编译的，因此每个文件都必须包含`const`修饰变量的定义。为了支持这一用法，并避免重复定义，**默认情况下`const`对象被设定为仅在文件内有效**。当多个文件中出现了同名的`const`变量时，等同于在不同文件中分别定义了独立的变量。

下面用一个例子说明上述内容：
```c++
// global.h
#ifndef DAY08_CONST_GLOBAL_H
#define DAY08_CONST_GLOBAL_H
const int bufSize = 100;
#endif //DAY08_CONST_GLOBAL_H

// global.cpp
#include "global.h"

// main.cpp
#include "global.h"
```
编译上述程序，程序可以编译通过，说明`global.cpp`和`main.cpp`中的`bufSize`虽然同名，但却是不同的变量。

如果不想定义不同的变量，则可以在`global.h`中用`extern`声明`bufSize`：
```c++
#ifndef DAY08_CONST_GLOBAL_H
#define DAY08_CONST_GLOBAL_H
const int bufSize = 100;
extern const int bufSize2;
#endif //DAY08_CONST_GLOBAL_H

//打印bufSize地址和bufSize2地址
extern void PrintBufAddress();
```
在`global.cpp`中定义：
```c++
#include "global.h"
const int bufSize2 = 10;

void PrintBufAddress(){
    std::cout << "global.cpp buf address: " << &bufSize << std::endl;
    std::cout << "global.cpp buf2 address: " << &bufSize2 << std::endl;
}
```
在`main.cpp`中调用`PrintBugAddress()`函数，并在`main.cpp`中打印两个变量的地址：
```c++
#include "global.h"
PrintBufAddress();
//输出bufSize地址
std::cout << "main.cpp buf address is " << &bufSize << std::endl;
//输出bufSize2地址
std::cout << "main.cpp buf2 address is " << &bufSize2 << std::endl;
```
输出如下：
```bash
global.cpp buf address: 0x7ff67a984040
global.cpp buf2 address: 0x7ff67a984044
main.cpp buf address is 0x7ff67a984000
main.cpp buf2 address is 0x7ff67a984044
```
可以看到`global.cpp`和`main.cpp`中的`bufSize`地址是不同的，而`bufSize2`是相同的。 

# `const`与引用
可以把引用绑定到`const`对象上，称之为常量的引用。与普通引用不同，常量的引用不能被用作修改它所绑定的对象：
```c++
const int ci = 1024;
const int &r1 = ci;
```
不能修改常量引用的值：
```c++
r1 = 2048; // 错误
```
**不能用非常量引用指向一个常量对象**：
```c++
int &r2 = ci; // 错误
```
允许用`const`修饰非`const`变量：
```c++
int i5 = 1024;
const int &r5 = i5;

i5 = 2048; // 正确
r5 = 2047; // 错误
```
**注意：此时可以使用变量名`i5`修改`i5`的值，但不能用别名`r5`进行修改。**
常量引用可以绑定字面值：
```c++
const int &r6 = 1024;
```
**`const`修饰的引用可以做隐式转换：**
```cpp
double dval = 3.14;
const int &ri = dval;
```
上述代码可以编译通过，将double类型的`dval`隐式转换为`int`类型。

# `const`与指针
## 指向常量的指针
可以让指针指向常量，此时该指针不能用于修改其所指对象的值.
```c++
const double PI = 3.14;
double *ptr = &PI; // 错误，普通指针不能指向常量
const double *cptr = &PI;
*cptr = 3.14; // 错误
```
**允许指向非常量的指针指向非常量**
```c++
int i10 = 2048;
const int *cptr2 = i10;
```

## `const`指针
允许将指针本身定义为常量，称之为常量指针。其一旦初始化，就不能再进行修改了，即不能指向其他地址。

把`*`放到`const`前用于表示指针是一个常量。
```c++
int errNumb = 0;
int *const curErr = &errNumb; // curErr是一个常量指针
const double pi2 = 3.14;
const double *const pip = &pi2; // pip是一个指向常量对象的常量指针
```
**指针本身是一个常量，并不意味着不能通过指针修改其指向的对象的值，能否修改由对象本身的类型决定。**
```c++
*pip = 2.72; //错误，pip是一个指向常量的指针
*curErr = 1024; //可以修改常量指针指向的内容
```

# 顶层`const`和底层`const`
> 用名词顶层`const`表示指针本身是常量，用名词底层`const`表示指针指向的对象是常量——《C++ Primer》
上述定义比较难以理解，可以按照下面两点来辨析`const`：
- 被修饰的变量本身无法改变的`const`是顶层`const`
- 通过指针或引用等间接途径来限制目标内容不可变的`const`是底层`const`
```c++
int i = 0;
int *const p1 = &i;       // 不能改变p1的值，这是一个顶层const
const int ci = 42;        // 不能改变ci的值，这是一个顶层const
const int *p2 = &ci;      // 允许改变p2的值，这是一个底层const
const int *const p3 = p2; // 靠右的const是顶层const，靠左的const是底层const
const int &r = ci;        // 用于声明引用的const都是底层const
```

# 参考
[【C++100问】深入理解理解顶层const和底层const](https://blog.csdn.net/TeFuirnever/article/details/103011514)


