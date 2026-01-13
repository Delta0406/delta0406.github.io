---
title: std::move与std::forward
date: 2025-06-11 16:40:33
tags: Modern C++
categories: c++基础
---

# 前言
本篇文章主要介绍`std::move`与`std::forward`的实现原理。

# static_cast
在讲解两个函数之前，首先需要了解`static_cast`的作用。`static_cast`是C++中的一种 显式类型转换 运算符，用于在类型之间安全地进行编译期转换。其基本语法如下：
```c++
static_cast<T>(expr) // 将expr转换为T类型
```
其主要用法有：
（1）用于基本数据类型之间的转换，如把int转换为char，把int转换成enum，但这种转换的安全性需要开发者自己保证（这可以理解为保证数据的精度，即程序员能不能保证自己想要的程序安全），如在把int转换为char时，如果char没有足够的比特位来存放int的值（int>127或int<-127时），那么static_cast所做的只是简单的截断，即简单地把int的低8位复制到char的8位中，并直接抛弃高位
（2）把空指针转换成目标类型的空指针
（3）把任何类型的表达式类型转换成void类型
（4）用于类层次结构中父类和子类之间指针和引用的转换
```c++
double d = 3.14;
int i = static_cast<int>(d); // 从 double 转成 int，结果是 3

class Base {};
class Derived : public Base {};

Derived d;
Base* pb = static_cast<Base*>(&d); // 子类 → 父类，安全

Base* pb2 = new Derived();
Derived* pd2 = static_cast<Derived*>(pb2); // 编译通过，但要小心类型是否真的匹配

void* pv = malloc(sizeof(int));
int* pi = static_cast<int*>(pv); // 从 void* 转回 int*，常见于 C 接口

enum Color { Red, Green, Blue };
int n = static_cast<int>(Green); // 枚举 → 整型
```

# std::move
`std::move()`函数主要用于获取右值引用，其实现如下：
```c++
/// include/bits/move.h
  template<typename _Tp>
    _GLIBCXX_NODISCARD
    constexpr typename std::remove_reference<_Tp>::type&&
    move(_Tp&& __t) noexcept
    { return static_cast<typename std::remove_reference<_Tp>::type&&>(__t); }
```
* `_GLIBCXX_NODISCARD`是一个宏，通常会展开为`[[nodiscard]]`，表示调用者不应忽略该函数的返回值
* `std::remove_reference<_Tp>::type&&`是函数的返回类型
  * `std::remove_reference<_Tp>::type`用于去掉`_Tp`上的引用（如果有）
  * `&&`表示返回该类型的右值引用
* `move(_Tp&& __t) noexcept`是函数名的参数部分
  * `_Tp&& __t`是万能引用（forwarding reference），它可以匹配左值引用或右值引用
  * noexcept 表示这个函数不会抛出异常
* `{ return static_cast<typename std::remove_reference<_Tp>::type&&>(__t); }`将`__t`显式地转成右值引用。这是实现“右值强制转换”的关键
下面给出一个使用的示例，以说明`std::move`的原理：
```c++
int x = 10;
int&& rx = std::move(x);  // ok，把 x 转成右值引用

int& a = x;
int&& ra = std::move(a);
```
x是左值，对应的`_Tp`为int，返回值为`int&&`。a的类型为`int&`，去掉引用后转为`int&&`。

# std::forward
> `std::forward`是C++中用于**完美转发（perfect forwarding）**的核心工具，它的目的是**在模板中把参数“原封不动”地传给另一个函数，保持它原本的左值或右值性质**。

万能引用不是已经可以获得右值引用吗？为什么还需要`std::forward`呢？给出如下示例：
```c++
void process(const Widget& lvalArg);        //处理左值
void process(Widget&& rvalArg);             //处理右值

template<typename T>                        //用以转发param到process的模板
void logAndProcess(T&& param)
{
    auto now =                              //获取现在时间
        std::chrono::system_clock::now();
    
    makeLogEntry("Calling 'process'", now);
    process(param);
}

Widget w;

logAndProcess(w);               //用左值调用
logAndProcess(std::move(w));    //用右值调用
```
我们希望传入左值实参和右值实参时，能够使用对应版本的`process()`函数进行处理，然而，C++中形参永远是左值，即使是如下函数，形参`w`依然是左值，因为`w`可以取地址。因此，和其他函数一样，`param`是一个左值，每次`logAndProcess()`调用内部函数`process()`时，都会调用它的左值重载版本。
```c++
void f(Widget&& w);
```
为了解决上述问题，就要用到`std::forward`，当`param`的实参是一个右值时，将`param`转换为右值：
```c++
void process(const Widget& lvalArg);        //处理左值
void process(Widget&& rvalArg);             //处理右值

template<typename T>                        //用以转发param到process的模板
void logAndProcess(T&& param)
{
    auto now =                              //获取现在时间
        std::chrono::system_clock::now();
    
    makeLogEntry("Calling 'process'", now);
    process(std::forward<T>(param));
}

Widget w;

logAndProcess(w);               //用左值调用
logAndProcess(std::move(w));    //用右值调用
```
** 是否`T&&`就没有意义了？**

答案是否定的，`T&&`和`std::forward`是配合使用的，用于在模板函数中实现完美转发，自动适配左值/右值。而在非末班函数中，`T&&`用于明确只接收右值。

# 参考
[性能优化利器 std::move/forward 实现原理 
](https://www.cnblogs.com/blizzard8204/p/17529803.html)
