---
title: 使用CRTP实现上下文限值
date: 2025-11-17 21:24:13
tags: 奇异递归模板
categories: 设计模式
---

# 前言
本工程使用CRTP实现编译阶段控制权限的Context数据访问框架。具体目标为：
> 给不同的节点 Node 提供访问 DictContext 的能力。同时用模板 + static_assert 保证：
Node 只能读 IN_KEYS，写 OUT_KEYS。否则编译报错。

# PermissionKey——Key的类型系统
```c++
// permissions_key.hpp
#ifndef PERMISSIONS_KEY_H
#define PERMISSIONS_KEY_H

#include <string>
template<typename T_tag, typename T>
struct PermissionKey {
    typedef T type;
    const char* name;
}

#define DEFINE_KEY(key_name, type) \
        struct key_name##_tag{}; \
        static constexpr PermissionKey<key_name##_tag,type>(key_name){#key_name}; \
        using key_name##_type = decltype(key_name);
        
DEFINE_KEY(NAME, std::string);
DEFINE_KEY(OLD, int);
DEFINE_KEY(TEL, std::string);
DEFINE_KEY(WORKID, std::string);
DEFINE_KEY(HEIGHT, float);

#endif
```
具体解释如下：
* 每个`Key`都是独立的类型（由tag唯一标识）
* 每个`Key`自带一个`value`类型（`type`），用于限定其对应的值类型
* 每个`Key`有一个字符串名字`name`，用于做运行时字典查找

以`DEFINE_KEY(NAME, std::string)`为例，其将会被展开为如下形式。即定义了一个独立的类型`NAME_tag`，并生成一个模板实例`PermissionKey<NAME_tag, std::string> NAME{"NAME"}`，`NAME`内部维护了它的类型`type`为`std::string`，名字为`NAME`。最后使用`NAME_type`来表示`PermissionKey`的一个实例，以用于后续的模板匹配。
```c++
struct NAME_tag{};
static constexpr PermissionKey<NAME_tag, std::string> NAME{"NAME"};
using NAME_type = PermissionKey<NAME_tag, std::string>;
```

# DictContext——字典容器，运行时存储Key-Value
`DictContext`是一个字典容器，其内部维护一个`unorder_map_`，用于存储键值对。通过`key.name`从字典中找到对应的值，然后通过`std::any_cast`将值转换为限定的类型`K::type`。

```c++
// dict_context.hpp
#include <unorder_map>
#include <string>
#include <any>
#include "permission_key.hpp"
#include <memory>

class DictContext {
public:
    typedef std::shard_ptr<DictContext> Ptr;
    
    template<typename K>
    typename K::type Get(K key) {
        auto iter = unordered_map_.find(key.name);
        if (iter != unordered_map_.end()) {
            return std::any_cast<typename K::type>(unordered_map_[key.name]);
        } else {
            throw std::runtime_error("Dict Context don't find the key");
        }
    }
    
    template<typename K>
    void Set(K key, typename K::type value) {
        unordered_map_[key.name] = value;
    }
    
private:
    std::unorder_map<std::string, std::any> unorder_map_;
}
```

# ContainKey/ContainAnyKey——编译期检查Key是否属于某个tuple列表
```c++
// contain_key_type_match.hpp
#include <tuple>
template<typename T, typename Tuple> struct ContainKey;
template<typename T> struct ContainKey<T, std::tuple<>>:std::false_type{};
template<typename T, typename Tfirst, typename... Trst>
struct ContainKey<T, std::tuple<Tfirst, Trst...>>: std::conditional<std::is_same<
    typename std::remove_const<T>::type,
    typename std::remove_const<Tfirst>::type>::value,
    std::true_type,
    ContainKey<T, std::tuple<Tfirst...>>>::type{};
    
template<typename T, typename... Tuples>
struct ContainAnyKey;

template<typename T>
struct ContainAnyKey<T>: std::false_type {};

template<typename T, typename First, typename... Rest>
struct ContainAnyKey<T, First, Rest...>:std::conditional<
    ContainKey<T, First>::value,
    std::true_type,
    ContainAnyKey<T, Rest...>
    >::type {};
```

# ContextHandle——提供get/set，并用static_assert做权限检查
```c++
// context_data_handle.hpp
#include "dict_context.hpp"
#include "contain_key_type_match.hpp"

class ContextHandle {
public:
    explicit ContextHandle(DictContext::Ptr dictContext): dictContextPtr_(std::move(dictContext)){};
    ~ContextHandle(){};
}

public:
    ContextHandle()=delete;
    ContextHandle(const ContextHandle&)=delete;
    ContextHandle& operator=(const ContextHandle&)=delete;
    ContextHandle(const ContextHandle&&)=delete;
    ContextHandle& operator=(const ContextHandle &&)=delete;
    
public:
    template<typename K, typename KFirst>
    typename K::type get(K key) {
        static_assert(ContainAnyKey<K, KFirst>::value, "The key is not be allowed to get!")
        return dictContextPtr_->Get(key);
    }
    
    template<typename K, typename KFirst, typename K2, typename ...Kest>
    typename K::type get(K key) {
        static_assert(ContainAnyKey<K, KFirst, K2, Kest...>::value, "The key is not be allowed to get!")
        return dictContextPtr_->Get(key);
    }
    
    template<typename K, typename KFirst>
    void set(K key, typename K::type value) {
        static_assert(ContainAnyKey<K, KFirst>::value, "The key is not be allowed to set!")
        dictContextPtr_->Set(key, value);
    } 
    
    template<typename K, typename KFirst, typename K2, typename ...Kest>
    void set(K key, typename K::type value) {
        static_assert(ContainAnyKey<K, KFirst, K2, Kest...>::value, "The key is not be allowed to set!")
        dictContextPtr_->Set(key, value);
    } 
    
private:
    DictContext::Ptr dictContextPtr_;
    
```

# BaseNode——为每个Node声明可读Key和可写Key
使用CRTP实现颠倒继承，父类`BaseNode`可以拿到子类`Derived`中的`IN_KEYS`和`OUT_KEYS`，在此基础上通过`ContextHandle`为子类添加权限检查功能。
```c++
// base_node_type.hpp

#include "dict_context.hpp"
#include "permission_key.hpp"
#include "contain_key_type_match.hpp"
#include "context_data_handle.hpp"

tempalte<typename Derived>
Class BaseNode {
public:
    BaseNode(DictContext::Ptr dictContextPtr): contextHandle_(dictContextPtr){}
    
public:
    template<typename K>
    typename K::type get(K key) {
        using IN_KEYS = typename Derived::IN_KEYS;
        using OUT_KEYS = typename Derived::OUT_KEYS;
        return contextHandle_.get<K, IN_KEYS, OUT_KEYS>(key);
    }
    
public:
    template<typename K>
    void set(K key, typename K::type value) {
        USING OUT_KEYS = typename Derived::OUT_KEYS;
        contextHandle_.set<K, OUT_KEYS>(key, value);
    }
    
public:
    ContextHandle contextHandle_;
}
```

# Node —— 指明本节点的权限
`Node`是`BaseNode<Node>的子类，其通过`IN_KEYS`和`OUT_KEUYS`决定可读`Key`和可写`Key`。

以`node.set(NAME, "xxx")`为例，我们来解释一下代码执行的流程：
1. 匹配到`Node::set`，因为Node没有自定义`set`调用`BaseNode::set`。此时：
* `K = NAME_type`
* `key = NAME`
* `value = std::string("xxx")`
* `OUT_KEYS = std::tuple<NAME_type, OLD_type, HEIGHT_type>`

2. 进入`BaseNode::set`→调用`ContextHandle::set`
此时匹配到`ContextHandle`的模板函数：
```c++
template<typename K, typename KFirst, typename K2, typename ...Krest>
void set(K key, typename K::type value)
```
其中：
* `K = NAME_type`
* `KFirst = OUT_KEYS = std::tuple<NAME_type, OLD_type, HEIGHT_type>`
* `没有 K2, Krest 参数`
因此，匹配到单参数版本的`set`：
```c++
template<typename K, typename KFirst>
void set(K key, typename K::type value) {
    static_assert(ContainAnyKey<K, KFirst>::value,
                  "The key is not be allowed to set!");
    dictContextPtr_->Set(key, value);
}
```

3. `static_assert`权限检查（编译期发生）
`ContainAnyKey`展开为`ContainKey`：
```c++
ContainKey<NAME_type, std::tuple<NAME_type, OLD_type, HEIGHT_type>>
```
此处为`true`，编译通过。
如果`NAME`不在`OUT_KEYS`中，编译期报错。

4. `ContextHandle`调用具体逻辑
```c++
dictContextPtr_->Set(key, value);
```

5. 进入`DictContext::Set`
```c++
template<typename K>
void Set(K key, typename K::type value) {
    unordered_map_[key.name] = value;
}
```
其中：
* `key.name = "NAME"`
* `value = std::string("xxx")`

```c++
// main.cpp
#include "context_data_handle.hpp"
#include <iostream>
#include "base_node_type.hpp"

class Node: public BaseNode<Node> {
public:
    Node(): BaseNode<Node>(std::make_shared<DictContext>()){}
    
    using IN_KEYS = std::tuple<WORKID_type, OLD_type, HEIGHT_type>;
    using OUT_KEYS = std::tuple<NAME_type, OLD_type, HEIGHT_type>;
};

int main(int argc, char** argv) {
    Node node{};
    node.set(NAME, "xxx");
    try {
        auto name = node.get(WORKID);
        std::cout << "my name: " << name << std::endl;
    } catch (std::exception e) {
        std::cerr << e.what() << std::endl;
    }
    
    node.set(HEIGHT, 1.50);
    auto height = node.get(HEIGHT);
    std::cout << "my height: " << height << std::endl;
    
    return 0;
}
```
