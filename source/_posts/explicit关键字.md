---
title: explicit关键字
date: 2025-09-24 23:04:56
tags: c++
categories: c++基础
---

# explicit的作用
在C++中`explicit`用来修饰类的构造函数，用于禁止隐式类型转换（只能显式调用构造函数）和禁止复制初始化（只能直接使用初始化）。

# explicit使用的注意事项
* `explicit`只能用于类内部的构造函数声明上。
* `explicit`关键字作用于单个参数的构造函数。

# 禁止隐式类型转换的示例
未加`explicit`时的隐式类型转换：
```c++
#include <iostream>
using namespace std;

class Point {
public:
    int x, y;
    Point(int x = 0, int y = 0)
        : x(x), y(y) {}
};

void displayPoint(const Point& p) 
{
    cout << "(" << p.x << "," 
         << p.y << ")" << endl;
}

int main()
{
    displayPoint(1);
    Point p = 1;
}
```
上面示例中的`Point`类定义了一个使用默认参数的构造函数，因此主函数中两行代码均会触发该构造函数的隐式调用（如果构造函数不使用默认参数，会在编译时报错）。

然而，`displayPoint`需要的是`Point`类型的参数，而传入的是一个`int`，隐式调用导致该程序能够运行成功。`explicit`关键字就是用来处理这样的情况，避免意外发生。
加上`explicit`的示例：
```c++
#include <iostream>
using namespace std;

class Point {
public:
    int x, y;
    explicit Point(int x = 0, int y = 0)
        : x(x), y(y) {}
};

void displayPoint(const Point& p) 
{
    cout << "(" << p.x << "," 
         << p.y << ")" << endl;
}

int main()
{
    displayPoint(Point(1));
    // displayPoint(1); // 错误：explicit禁止隐式类型转换
    Point p(1);
}
```
加上`explicit`后，`displayPoint`函数中就被禁止进行隐式转换，必须传入`Point`类型的实参。

# 禁止复制初始化示例
```c++

#include <iostream>

class Baz {
public:
    explicit Baz(int) {}
};

int main() {
    Baz b1(42);       // ✅ 直接初始化
    // Baz b2 = 42;   // ❌ 错误：explicit 禁止复制初始化
}
```