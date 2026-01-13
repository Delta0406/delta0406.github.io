---
title: 类型推导——auto与decltype
date: 2025-06-09 09:25:18
tags: [Modern C++,类型推导]
categories: c++基础
---

# 前言
编码时必须明确变量的类型会降低编码的效率，并使代码变得冗长。因此，C++提供了auto和decltype这两个关键字来实现类型的推导。

# auto
## 基本语法
auto的基本语法如下：
```c++
auto variable_name = expression;
```
编译器可以根据expression的类型来自动推导出variable_name的类型。

## 使用示例
auto比较常见的用法是推导迭代起来类型的推导：
```c++
int x = 5;
auto a = x;          // a 被推导为 int

double d = 3.14;
auto b = d;          // b 被推导为 double

std::vector<int> vec = {1, 2, 3};
auto it = vec.begin(); // it 被推导为 std::vector<int>::iterator
```

## 注意事项
* auto必须初始化
```c++
auto x; // 错误
```
* 常量性和引用修饰符不自动保留
```c++
const int ci = 42;
auto a = ci;     // a 是 int，不是 const int

int x = 10;
int& r = x;
auto b = r;      // b 是 int，不是 int&
```
如果想要保留修饰符，需要手动加上：
```c++
auto& c = r; // c 是 int&

const auto d = ci; // d 是 const int
```

## C++14用法增强
* 函数返回类型自动推导
```c++
auto add(int a, int b) {
    return a + b;
}
```
* 泛型lambda函数传参
```c++
auto func = [](auto x, auto y) {
    return x + y;
}

func(1, 2); // 3
func(1.5, 2.5); // 4.0
```
## C++20用法增强
* 一般函数传参
```c++
int add(auto x, auto y) {
    return x + y;
}
std::cout << add(5, 6) << std::endl;
```

## 万能引用（转发引用）
auto&&是C++11引入的一种万能引用，可以根据初始化表达式的值类型（左值/右值）推导出不同的类型。给定如下代码，编译器会根据expr的值类型，推导出x的类型：
```c++
auto&& x = expr;
```
通过使用auto&&，可以绑定左值也可以绑定右值的引用类型：
```c++
int a = 42;
auto&& x = a; // 左值
auto&& y = 123; // 右值
```
### 使用场景
* 泛型代码的完美转发
```c++
template<typename T>
void wrapper(T&& arg) {
    func(std::forward<T>(arg)); // 完美转发
}
```
其中 T&& 是模板参数的万能引用，auto&& 是其非模板变量形式，两者原理相似。

* 范围for循环中高效使用
```c++
std::vector<std::string> v = {"hello", "world"};

for (auto&& s : v) {
    // s 是 std::string&，防止复制，提高效率
    std::cout << s << std::endl;
}
```
如果你不确定容器中元素是左值还是右值、是否能被修改，auto&& 是一种保险、灵活又高效的选择。

# decltype
## 基本语法
auto关键字只能对变量类型进行推导，为了解决这一缺陷，引入了decltype，其用法如下：
```c++
decltype(表达式)
```

## 使用示例
```c++
auto x = 1;
auto y = 2;
decltype(x+y) z;
```

# 尾返回类型推导
能否直接使用decltype推导函数的返回类型呢？就像下面的代码这样：
```c++
template<typename T, typename U>
decltype(x, y) add(T x, U y) {
    return x + y;
}
```
答案是不能的，这样写无法通过编译。因为编译器在读到decltype(x+y)时，x和y还没有被定义。为此，C++11引入了尾返回类型，利用auto关键字返回类型后置：
```c++
template<typename T, typename U>
auto add(T x, U y) -> decltype(x + y) {
    return x + y;
}
```
**其中，auto是用于配合尾返回类型的占位符，->decltype(x + y)表示返回类型是表达式x + y的类型。这样写的好处是即使在模板定义中的T和U类型不同，也能正确推导出返回值的实际类型。例如int + double会返回double。**

C++14开始可以直接让普通函数具备返回值推导，因此下面的写法变得合法：
```c++
template<typename T, typename U>
auto add2(T x, U y){
    return x + y;
}
```

# decltype(auto)
decltype(auto)是C++14开始提供的用法，其主要用于对转发函数或封装的返回类型进行推导，而无需显示地指定。例如，对于下面的两个函数：
```c++
std::string lookup1();
std::string& lookup2();
```
在C++中，封装实现的形式如下：
```c++
std::string look_up_a_string_1() {
    return lookup1();
}
std::string& look_up_a_string_2() {
    return lookup2();
}
```
而使用decltype(auto)则可以让编译器完成参数的转发，无需显示指定参数类型：
```c++
decltype(auto) look_up_a_string_1() {
    return lookup1();
}
decltype(auto) look_up_a_string_2() {
    return lookup2();
}
```

# 参考
[Modern C++](https://changkun.de/modern-cpp/zh-cn/02-usability/)


