---
title: C++内存管理机制——std::allocator
date: 2025-10-22 22:16:55
tags: 内存管理
categories: c++基础
---

# malloc
## vc6.0 malloc
![vc6.0 malloc](./images/内存管理/vc6_malloc.png)

上图展示了VC6.0中`malloc()`函数分配的内存。vc6.0的`malloc()`是一定会携带cookie的，且固定占用8个字节。蓝色部分是申请的内存，假定为12个字节，表示为16进制下的0xC。debug heder和tail由灰色的块组成，每个块4个字节，因此共占32+4个字节。上下cookie占用4*2个字节。上述所有信息共占据`0xC+(32+4)+4*2=0x38`个字节，不是16的倍数，因此padding8个字节，共需要`0x40`个字节。客户端实际得到的是指向`fill 0xcd`的指针。

可以看到，除了所需申请的内存空间外还有cookie、debug信息和pad。其中，cookie是我们不需要的，如果大量调用`malloc()`的话cookie总和会增多，造成较大的浪费。

![VC6.0 标准分配器实现](./images/内存管理/vc6_allocator_implement.png)
VC6.0的标准分配器使用`::operator new`和`::operator delete`实现`allocate()`和`deallocate`，本质都是对`malloc()`的封装。其是以类型字节长度为单位分配内存的，上图中分配了512个`int`类型空间。

## bc5 allocator
![bc5 标准分配器实现](./images/内存管理/bc5_malloc_implement.png)

## G2.9 allocator
![G2.9 标准分配器实现](./images/内存管理/g2_9_malloc_implement.png)

G2.9版本的allocator实现如上图所示，但其并没有实际使用。实际上，G2.9是使用了一个`alloc`类实现内存管理，该类分配内存以**字节**为单位，而非对象。如下图所示：

![G2.9 alloc](./images/内存管理/g2_9_alloc.png)

## GCC4.9 allocator
GCC4.9版本将GCC2.9里不属于正式使用的版本`std::alloc`转变成`_pool_alloc`，修改了变量名和部分操作。
![std::alloc vs _pool_alloc1](./images/内存管理/pool_alloc_1.png)

![std::alloc vs _pool_alloc2](./images/内存管理/pool_alloc_2.png)

而GCC4.9的标准分配器实现仍是以`::operator new`和`::operator delete`实现，没有特殊设计。

![G4.9 标准分配器实现](./images/内存管理/g4_9_standard_implement1.png)

![g4.9 pool allocator 用例](./images/内存管理/g4_9_pool_allocator.png)
对`_pool_alloc`和标准分配器进行测试，从输出结果可以看出，使用`_pool_alloc`分配内存，连续两块内存之间的距离是8，而一个double类型变量的大小也是8个字节，说明这些分配的内存之间是不带cookie的。而如果使用标准分配器，相邻两块内存之间的距离为16个字节，每块内存带有一个4字节的头和4字节的尾。

# std::alloc
## std::alloc运行模式
> 供容器使用，因为容器中元素占用的内存大小一致

`std::alloc`使用一个16个元素的数组来管理内存链表，每个元素用来管理不同的区块。例如`#3`号元素负责管理32字节大小的内存块的链表。

假设用户当前需要大小为32字节的内存，`std::alloc`会先申请一块区间，大小为`32*20*2`字节，用链表进行管理，数组中`#3`元素负责管理这条链表。函数会返回这个链表中的第一个元素给用户。链表的前`32*20`的内存空间是分配给用户的，而后`32*20`的空间是预留的，如果用户需要额外的大小为64字节的内存，预留的`32*20`的内存空间将会被转换为`64*10`供用户使用，而无需再一次构建链表和申请空间，使用数组中的`#7`元素来管理这块`64*10`的空间。

数组管理的内存是有上限的，如果该数组维护的链表组最大的内存块大小为128字节，当用户申请内存超过128字节时，`std::alloc`将会调用`malloc()`为用户分配空间，并在该内存块上带上cookie头和尾。
![std::alloc运行模式](./images/内存管理/std_alloc运行模式总览.png)

在商业级的内存分配器中，一般会使用嵌入式指针（embedded pointers），将每个内存块的前四个字节用作指针连接下一块可用的内存块。当内存块被分配出去时，指针被覆盖写入用户数据，空闲链表指针指向下一块空闲内存块。归还内存时，再往内存块内部写入指针，指向下一块空闲内存。

![embedded pointers](./images/内存管理/embedded_pointers.png)

> 为什么嵌入式指针会搭配`union`使用？
> 
> 因为我们想要复用内存，让同一块内存在不同阶段承担不同的角色。当对象处于空闲状态时，我们需要一块指针将它串在空闲链表上。但当对象处于使用状态时，我们希望这块内存用于存储真实数据。
> 
> `union`为同一内存区域提供了多重解释能力。C/C++语言规定`union`的所有成员共享同一块内存，并且这块内存的尺寸就是最大成员的大小。

## `std::alloc`运行一瞥
![std::alloc运行一瞥01](./images/内存管理/std_alloc_01.png)

链表上方小块表示cookie。
![std::alloc运行一瞥02](./images/内存管理/std_alloc02.png)
![std::alloc运行一瞥03](./images/内存管理/std_alloc03.png)

`RoundUp`是追加量，值为目前累计申请量除以16，以适应越来越高的内存要求。
![std::alloc运行一瞥04](./images/内存管理/std_alloc04.png)

申请内存时，首先看战备池是否有足够的内存，如果有则直接从池中分配。
![std::alloc运行一瞥05](./images/内存管理/std_alloc05.png)
![std::alloc运行一瞥06](./images/内存管理/std_alloc06.png)
![std::alloc运行一瞥07](./images/内存管理/std_alloc07.png)
![std::alloc运行一瞥08](./images/内存管理/std_alloc08.png)
![std::alloc运行一瞥09](./images/内存管理/std_alloc09.png)
![std::alloc运行一瞥10](./images/内存管理/std_alloc10.png)
![std::alloc运行一瞥11](./images/内存管理/std_alloc11.png)
![std::alloc运行一瞥12](./images/内存管理/std_alloc12.png)
![std::alloc运行一瞥13_01](./images/内存管理/std_alloc13_01.png)
![std::alloc运行一瞥13_02](./images/内存管理/std_alloc13_02.png)

## std::alloc源码剖析
### 二级分配器
`std::alloc`分配器使用的是`_default_alloc_template`，在该类中定义了一个`ROUND_UP`函数，用来将申请内存数量做16字节的对齐。此外，还定义了一个`free_list_link`用于指向指向链表的指针，即嵌入指针。`free_list`则是我们前面介绍的用来管理链表的数组，共有16个`obj*`类型的元素。`start_free`和`end_free`分别指向内存池的头和尾，`heap_size`用于记录分配的累计量。
![std::alloc源码剖析4](./images/内存管理/std_alloc_源码剖析4.png)

#### 分配与回收
首先介绍第二级的分配和回收函数。`allocate`中定义了一个`my_free_list`，用于指向`free_list`中的元素。对其解引用，取出`free_list`元素中的值，该值指向一条分配内存的链表。`result`则保存分配给用户的内存块的地址。对于内存分配请求，需要先检查申请分配的内存大小，如果大于`_MAX_BYTES`那么调用第一级分配方法进行分配。如果小于，将根据用户申请内存大小分配对应的内存，，由于内存池使用`free_list`链表进行管理，需要先定位到对应的位置，并从中取出空闲内存块地址，用`result`保存。如果`result`为空，说明内存不足，将会使用`refill()`函数分配内存。如果不为空，则将该链表中下一个可以使用的内存块地址设置为当前分配给用户的内存块指向的下一个内存块。最后将`result`返回给用户。
![std::alloc源码剖析5](./images/内存管理/std_alloc_源码剖析5.png)
![std::alloc源码剖析5_02](./images/内存管理/std_alloc_源码剖析5_02.png)

释放内存则需要先判断待释放的内存空间是否属于二级分配器管理，不属于则调用一级分配器处理。属于则拿到待释放内存对应的空闲链表，将待释放内存块的`free_list_link`指向拿到的空闲链表表头，并设置空闲链表表头为待释放内存块。
![std::alloc源码剖析5_03](./images/内存管理/std_alloc_源码剖析5_03.png)

#### refill
`refill()`预设一个20个区块数`nobjs`，接着通过`chunk_alloc(n, nobjs)`申请内存。这里并不一定会真的申请到20块内存块，因此使用的是引用传递。拿到内存后，判断是否返回的是一块内存，如果是一块直接返回给申请方即可。否则在chunk内构建空闲链表。
![std::alloc源码剖析8](./images/内存管理/std_alloc_源码剖析_8.png)

#### chunk_alloc
函数开始计算了一些必要的值：`result`指向分配给用户的内存，`total_bytes`为需要分配的内存块的大小，`bytes_left`则是当前内存池中剩余的空间大小。

接着，判断内存池剩余的内存大小是否满足需要分配的内存块大小：
* 如果满足，则将内存池的首地址`start_free`赋值给`result`，然后将`start_free`指针下移`total_bytes`距离，返回`result`。
* 如果`byte_left`比`total_bytes`小，但比`size`大，则先计算能够分配多少个块`nob js`给用户，重新计算`total_bytes`。然后将该块分配给用户，`start_free`指针移动`total_bytes`长度。
* 否则，需要向系统申请内存。`bytes_to_get`表示需要申请的内存大小。首先会对内存碎片进行回收，将剩余内存插入对应的空闲链表，确保没有内存碎片。紧接着就利用`malloc()`向系统申请`bytes_to_get`大小的内存。
  * 如果成功，则计算累计分配量，并更新`end_free`。此时已有足够内存，所以递归调用`chunk_alloc`为用户分配内存。
  * 如果失败，在数组中向右查找空闲链表中可用的内存空间。当空闲链表内有可用区块时，释放一块给申请内存的池使用，递归调用`chunk_alloc`分配内存。如果右边的空闲链表全部为空，则设置`end_free`为0，改为调用第一级的分配函数，用`oom_handler`处理。

![std::alloc源码剖析6](./images/内存管理/std_alloc_源码剖析6.png)
![std::alloc源码剖析7](./images/内存管理/std_alloc_源码剖析7.png)

#### 变量初始化
![std::alloc源码剖析9](./images/内存管理/std_alloc_源码剖析9.png)


### 一级分配器
一级分配器叫做`__malloc_alloc_template`，源码如下，`allocate()`函数直接调用的`malloc()`分配内存，如果失败则调用`oom_malloc()`。`deallocate()`直接使用`free()`释放内存。`set_malloc_handler()`则是一个函数指针，传入一个`void(*f)()`类型函数，该函数可以用于设置内存不够情况下的错误处理函数，由用户来进行管理。
![std::alloc源码剖析1](./images/内存管理/std_alloc_源码剖析1.png)

一级分配器的别名为`malloc_alloc`：
```c++
typedef __malloc_alloc_template<0>  malloc_alloc;
```

`reallocate()`也是一样的操作：
```c++
  static void* reallocate(void *p, size_t /* old_sz */, size_t new_sz)
  {
    void * result = realloc(p, new_sz); //直接使用 realloc()
    if (0 == result) result = oom_realloc(p, new_sz);
    return result;
  }
```

`set_malloc_handler`是一个函数指针，里面传入一个`void(*f)()`类型函数：
```c++
static void (*set_malloc_handler(void (*f)()))()
{ //類似 C++ 的 set_new_handler().
  void (*old)() = __malloc_alloc_oom_handler;
  __malloc_alloc_oom_handler = f;
  return(old);
}
```
该函数用于设置内存分配不足情况下的错误处理函数，由用户进行管理。首先保存先前的处理函数，然后再将新的处理函数赋值给`__malloc_alloc_oom_handler`，返回旧的处理函数。

`oom_malloc`内部则不断调用用户设置的错误处理函数`__malloc_alloc_oom_handler`,并再次尝试通过`malloc`申请内存。`oom_realloc`也是遵循相同的处理方式。

![oom_malloc](./images/内存管理/oom_malloc.png)

### std::alloc观念整理
当我们使用容器去管理对象时，如果直接放入临时对象`Foo(1)`，则直接没有cookie。而如果放入`new`出来的在堆中的对象，则会copy一份内容进容器。`new`出来的对象是使用的`malloc`，携带cookie，放入容器则节省了cookie的空间。
![std::alloc观念整理1](./images/内存管理/std_alloc观念整理1.png)


# 参考
[CPP-Memory-Management](https://github.com/hujiese/CPP-Memory-Management/tree/master)

[侯捷-C++内存管理机制](https://www.bilibili.com/video/BV1d3h5zFEjL?spm_id_from=333.788.videopod.sections&vd_source=cb2ffbc722372d15094f9eebc2c1e0a4)

