---
title: const和constexpr详解
date: 2025-06-06 15:57:13
tags: c++
categories: c++基础
---

# 前言
constexpr是c++11引入的关键字，其和const都是用来定义常量的，本文将详解两者的区别。

# const
const一般用于修饰变量、引用、指针，标记它们为常量。然而，const并未区分编译期常量和运行期常量，只能保证变量运行时不被直接修改。

const变量，其值不能发生改变：
```c++
const int x = 100; // 常量
x = 200; // 无法通过编译
```
const引用，无法通过引用修改变量的值：
```c++
int x = 10;
const int& ref = x;
// ref = 20; // 无法通过编译
x = 20; // 通过编译
cout << "ref = " << ref << endl; // 输出：ref = 20。虽然不能通过ref直接修改变量值，但可以通过x修改
```
const引用，不能通过指针修改其所指向的值，但指针本身可以指向其他的地址：
```c++
int a = 10;
int b = 20;
const int* ptr = &a;
// *ptr = 5; // 错误，不能修改指针指向变量的值
ptr = &b; // 正确，可以修改指针指向
```
**指向常量的指针的指向可以发生改变，若要限制指针本身为常量，需要调整const的位置：**
```c++
int* const ptr = &a; // 指针地址不能改变，但是可以通过指针修改指向变量的值
const int* const ptr2 = &a; // 指向常量的常量指针，既不能通过指针修改值，也不能修改指针地址
```
此外，const还能修饰成员函数，表明该函数不会修改对象的状态（成员变量）：
```c++
class TestClass {
private:
    const long MAX_SIZE = 256;;
    int m_value;

public:
    int get_value() const {
        m_value = 100; // 错误，不能修改成员变量的值
        return m_value;
    }
}
```

# constexpr
const并没有区分编译期常量和运行期常量，我们用下面这个例子来说明：
```c++
#include <cstdlib>

int getValue() {
    return rand() % 100;
}

int main() {
    const int x = getValue();  // x 是 const，但不是编译期常量
    int arr[x];                // 错误：x 不是编译期常量，不能做数组大小
}
```
> 编译期程序还没开始运行，只有字面值常量可以确定
> 
> 运行期所有表达式都能求值

constexpr即constant expression（常量表达式），进一步将修饰的内容限定为编译期常量。

constexpr修饰变量时，编译器能在编译时确定变量值：
```c++
constexpr int x = 5; // 编译期常量
int arr[x];          // 数组大小合法
```

constexpr修饰函数时，当其参数是constexpr时，函数会生成编译期常量。而使用非constexpr变量调用时，在运行时生成值：
```c++
constexpr int square(int x) {
    return x * x;
}

constexpr int val = square(10); // 编译期求值
```
非constexpr值，则当做普通函数使用：
```c++
constexpr int square(int x) {
    return x * x;
}

int x = rand();
int y = square(x); // 合法，作为普通函数使用
```

# 参考
[C++ 中让人头晕的const & constexpr](https://www.luozhiyun.com/archives/756)
[constexpr (C++)](https://learn.microsoft.com/zh-cn/cpp/cpp/constexpr-cpp?view=msvc-170#constexpr_functions)



