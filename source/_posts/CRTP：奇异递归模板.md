---
title: CRTP：奇异递归模板
date: 2025-11-17 20:40:27
tags: 奇异递归模板
categories: 设计模式
---

# 前言
CRTP（Curiously Recurring Template Pattern），奇异递归模板是一种特征的模板技术，其特征为：
* 基类是一个模版类
* 派生类继承该基类时，将派生类自身作为模板参数传递给基类

# CRTP范例
CRTP的一个范例如下，`Base`类通过`static_cast`将基类指针转换为派生类。由于没有动态类型检查，这个过程是不一定安全的。但`Base<Derived>`是利用子类信息生成的，即`static_cast`是一定绑定到`Derived`上的，不会出现错误。此外，`static_cast`执行的前提是`Derived`必须是`Base<Derived>`的子类，这就保证了模板参数`T`的实参和`Base`之间的继承关系，因此转换能够保证安全。
> `static_cast`不安全是因为它不会做动态类型判断，但它要求两者之间的继承关系在编译期已知。
> CRTP能够在模板实例化时固定继承关系 

```c++
// 基类是模板类
template <typename T>
class Base
{
public:
    virtual ~Base() {}
 
    void func()
    {
        if (auto t = static_cast<T *>(this))
        {
            t->op();
        }
    }
};
 
// 派生类Derived继承自Base，并以自身作为模板参数传递给基类
class Derived : public Base<Derived>
{
public:
    void op()
    {
        std::cout << "Derived::op()" << std::endl;
    }
};
```

# CRTP的用法
## 静态多态
多态是指同一个方法在基类和不同的派生类之间有不同的行为。CRTP中每个派生类继承的基类随着模板参数的不同而不同，将虚函数调用转换为函数指针的调用，能够避免通过指针查找虚函数表的开销，提高计算效率。
```c++
template <typename T>
class Base
{
public:
    Base() {}
    virtual ~Base() {}
 
    void func()
    {
        if (auto t = static_cast<T *>(this))
        {
            t->op();
        }
    }
};
 
class Derived1 : public Base<Derived1>
{
public:
    Derived1() {}
    void op()
    {
        std::cout << "Derived1::op()" << std::endl;
    }
};
 
class Derived2 : public Base<Derived2>
{
public:
    Derived2() {}
    void op()
    {
        std::cout << "Derived2::op()" << std::endl;
    }
};
 
// 辅助函数：完成静态分发
template<typename DerivedClass>
void helperFunc(Base<DerivedClass>& d)
{
    d.func();
}
 
int main(int argc, char* argv[]) 
{
    Derived1 d1;
    Derived2 d2;
    helperFunc(d1);
    helperFunc(d2);
 
    return 0;
}
```
运行结果：
```bash
Derived1::op()
Derived2::op()
```

## 颠倒继承
> 通过父类向子类添加功能：可以从子类中获取信息，在父类中统一实现某个功能

我们以`InternalQueueBase`类为例，展示颠倒继承的作用。`InternalQueueBase`内部实现了一个`Node`类，它的`next`和`prev`函数利用颠倒继承和`reinterpret_cast`的强制类型转换，让父类获得了返回子类指针的能力，从而让子类通过继承拥有了对应的能力。
```c++
template <typename LockType, typename T>
class InternalQueueBase {
 public:
  struct Node {
   public:
    Node() : parent_queue(NULL), next_node(NULL), prev_node(NULL) {}
    virtual ~Node() {}

    /// Returns the Next/Prev node or NULL if this is the end/front.
    T* next() const {
      boost::lock_guard<LockType> lock(parent_queue->lock_);
      return reinterpret_cast<T*>(next_node);
    }
    T* prev() const {
      boost::lock_guard<LockType> lock(parent_queue->lock_);
      return reinterpret_cast<T*>(prev_node);
    }

   private:
    friend class InternalQueueBase<LockType, T>;

    Node* next_node;
    Node* prev_node;
  };
```

这里的`Block`通过`CRTP`的方式继承了`InternalQueue<Block>::Node`，于是自动成为线程安全的`Queue`中的节点，而`Block`类的`next`和`prev`方法可以自动返回指向`Block`的指针。
```c++
 class Block : public InternalQueue<Block>::Node {
    public:
        // A null dtor to pass codestyle check
        ~Block() {}
```

# 参考
[【C++】CRTP：奇异递归模板模式](https://blog.csdn.net/sinat_21107433/article/details/123145236)
[C++雾中风景14:CRTP, 模板的黑魔法](https://www.cnblogs.com/happenlee/p/13278640.html)