---
title: C++程序编译过程
date: 2025-05-22 15:46:48
tags: c++
categories: c++基础
---

# 前言
C++程序编译过程主要分为以下四个阶段：
1. 预处理（Preprocessing）：在编译器真正编译源代码之前对代码进行处理，这个阶段由预处理器完成，主要处理以`#`开头的预处理指令。
2. 编译（Compilation）：将预处理后的C++源代码转换成汇编代码。
3. 汇编（Assemble）：将编译器生成的汇编代码转换为目标机器能够理解的机器代码。
4. 链接（Linking）：将多个目标文件和库文件（如标准库、第三方库）合并成一个可执行文件。

# 示例
首先介绍示例代码，总共包含三个文件`main.cpp`、`my_math.h`和`my_math.cpp`。

`main.cpp`代码如下：
```c++
#include <iostream>
#include "my_math.h"
using namespace std;

int main() {
	int a = 10;
	int b = 20;
	int s = demo::sum(a, b);
	cout << "s = " << s << endl;
	return 0;
}
```

`my_math.h`代码如下：
```c++
#ifndef MY_MATH_H
#define MY_MATH_H

namespace demo {
	int sum(int a, int b) {
		return a + b;
	}
}
#endif
```

`my_math.cpp`代码如下：
```c++
#include "my_math.h"

namespace demo {
	int sum(int a, int b) {
		return a + b;
	}
}
```

## 预处理
预处理阶段主要处理以`#`开头的代码行，例如对宏做展开、对include的文件做展开、条件编译选项判断、清理注释等。预处理后的文件以`.i`和`.ii`结尾。

在Visual Studio中可以在项目的属性中将下图两个字段设置为是，以生成预处理文件：
![生成预处理文件设置](./images/C++程序编译过程/生成预处理文件设置.png)
**注意：设置了预处理到文件之后将不在生成可执行文件，Linker将无法找到要链接的可编译目标obj文件，要想生成可执行文件需要将预处理到文件重新设置为否。**

设置完毕后，生成解决方案，即可在项目文件夹（项目文件夹/项目文件名/x64/Debug）中找到对应的.i文件，下图展示了`main.i`文件。从图中可以看出简单的代码经过预处理后展开成了几万行的代码。
![main预处理文件](./images/C++程序编译过程/main预处理文件.png)

## 编译
编译器（如g++、clang++等）使用预处理的输出结果作为输入，生成与平台相关的汇编代码，文件以`.s`或`.asm`结尾。

在Visual Studio中，右键项目，进入属性。在左侧配置属性，选择C/C++中的输出文件。接着找到选项汇编程序输出，将其更改为带源代码的程序集，即可在`项目文件夹/项目文件名/x64/Debug`文件夹下得到汇编文件。
![输出汇编文件设置](./images/C++程序编译过程/输出汇编文件设置.png)
![main汇编文件](./images/C++程序编译过程/main汇编文件.png)

## 汇编
汇编将编译阶段产生的汇编代码转换为目标代码，通常以`.o`、`.obj`或`.out`结尾。

C++程序在生成解决方案时会自动生成目标代码，代码位于`项目文件夹/项目文件名/x64/Debug`文件夹下。

## 链接
链接阶段将目标文件和库文件合并成一个可执行文件或库文件。在链接的过程中，链接器会解决外部符号引用（即函数和变量的调用），并将它们链接到正确的地址。该阶段的输出为以`.exe`结尾的文件。

# 理解类模板成员函数生成的时机
模板本质上是编译期的代码生成机制。

接下来给出一个模版类的范例，以更好地理解类模版成员函数的生成机制：
```c++
class Person1 {
public:
    void showPerson1() {
        cout << "Person1 show" << endl;
    }
};

class Person2 {
public:
    void showPerson2() {
        cout << "Person2 show" << endl;
    }
};

template<class T>
class MyClass {
public:
    T obj;


    void fun1() {
        obj.showPerson1();
    }

    void fun2() {
        obj.showPerson2();
    }
};

void test01() {
    MyClass<Person> m;

    m.fun1(); // 编译成功
}

void test02() {
    MyClass<Person> m;

    m.fun1();

    m.fun2(); // 编译失败
}
```
当我们调用`test01()`时，编译器在编译阶段发现用`MyClass<Person>`类进行了实例化，并调用了`showPerson1()`函数，会为`Person`类型生成`MyClass<Person>::showPerson1()`的代码。而`showPerson2()`没有被调用，因此编译器不会为其生成代码，也不会参与后续的汇编和链接阶段。

**这样设计的好处：可以避免不必要的代码生成，节省资源。**

以`MyClass<T>`

# 参考
[visual Studio 如何查看预处理后生成的代码C/C++](https://blog.csdn.net/Applicaton/article/details/127437265?spm=1001.2101.3001.6650.3&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7Ebaidujs_baidulandingword%7ECtr-3-127437265-blog-145368757.235%5Ev43%5Epc_blog_bottom_relevance_base3&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7Ebaidujs_baidulandingword%7ECtr-3-127437265-blog-145368757.235%5Ev43%5Epc_blog_bottom_relevance_base3&utm_relevant_index=3)
[C/C++程序编译过程为什么要分为四个步骤？](https://zhuanlan.zhihu.com/p/549996872)


