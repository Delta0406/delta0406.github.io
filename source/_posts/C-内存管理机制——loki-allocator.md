---
title: C++内存管理机制——loki::allocator
date: 2025-11-24 19:47:12
tags: 内存管理
categories: c++基础
---

# 上中下3个class
`loki::allocator`中包含3个类，从上层至下层分别为`SmallObjAllocator`、`FixedAllocator`和`Chunk`。

![3 classes](./images/内存管理/暂存/内存管理_129.jpg)

# Chunk
`Init`是由上层的类来调用的，不会提供给用户。其会申请`blockSize * blocks`大小的内存，并调用`Reset`来重置第一块可以使用的的内存索引`firstAvailableBlock_`为0，可使用的块数量`blocksAvailable_`为`blocks`。随后，将内存块中每个块的最前面的一个字节当做索引，与嵌入式指针类似。`Release`是用来释放`Chunk`申请的内存的。

![Chunk](./images/内存管理/暂存/内存管理_137.jpg)

接下来，探索索引的变化规则。假设当前的编号为`5012367...64`，通过`Chunk::Allocate()`申请内存，首先查`Chunk`的`firstAvaliableBlock_`，发现第一个可用内存块的索引为4，于是找到图中索引为3的位置，并将其置为使用状态，`firstAvaliableBlock_`变更为3，`blocksAvailable_`减1变更为63。

![Chunk::Allocate()](./images/内存管理/暂存/内存管理_138.jpg)

在执行`Deallocate(p, blockSize)`前，会先通过遍历找到p属于哪个`Chunk`，p减去`Chunk`的首地址，再被除以`blockSize`即可确定p的位置。然后将p对应的索引设置为`firstAvaliableBlock_`，`blocksAvailable_`加1。

![Chunk::Deallocate()](./images/内存管理/暂存/内存管理_139.jpg)

# FixedAllocator
`FixedAllocator`的成员如下代码所示，其中`allocChunk_`指向上一次满足分配的`Chunk`，`deallocChunk_`指向上一次释放的`Chunk`，这也很符合内聚性。

```c++
chunks_: vector<Chunk>
allocChunk_: Chunk*
deallocChunk_: Chunk*
```

`FixedAllocator`分配时首先判断`allocChunk_`是否为空或没有可以块，如果是上述情形，则暴力遍历`chunks_`。如果找到有可用块的`Chunk`，则让`allocChunk`指向该`Chunk`，调用`Chunk::Allocate()`进行分配。如果没找到，`new`一个新`Chunk`挂载在`chunks_`的末端，并初始化。`allocChunk_`指向这块新创建的`Chunk`，`deallocChunk_`指向`chunks_`的前端（因为新创建`Chunk`后，`chunks_`不一定还在原来的位置，可能被复制到其他位置，如果`deallocChunk_`指向的位置还是原来的位置可能会出现异常，因此把该指针指向最新的`chunks_`的前端）。

![FixedAllocator](./images/内存管理/暂存/内存管理_140.jpg)

`FixedAllocator`释放时首先通过`VicinityFind()`找到块所在的位置。首先定义`lo`和`hi`两个指针，在循环中从`deallocChunk_`和`deallocChunk_ + 1`向`chunks_`的两端进行搜索，直到找到所在的`Chunk`。

**这里存在一个bug，如果p并非由此系统取得，会跳不出循环**

![VicinityFind()](./images/内存管理/暂存/内存管理_141.jpg)

`DoDeallocate()`会调用`deallocChunk_`的`Deallocate()`方法进行回收，并判断其可用内存块数量`blockAvailable_`是否等于分配的内存块数量`numBlocks`。如果等于，则进行如下三个判断：
1. 如果`deallocChunk_`是`chunks_`的最后一个区块，且`chunks_`的大小大于1及`deallocChunk_`的前一个`Chunk`所有的区块也为空，则释放`chunks_`的最后一个区块。
2. 如果最后一个`Chunk`的所有块为空，释放最后一个区块，并令`allocChunk_=deallocChunk_`。
3. 否则，将`deallocChunk_`一道`chunks_`的末端。

![DoDeallocate()](./images/内存管理/暂存/内存管理_142.jpg)

# 参考
[侯捷-C++内存管理机制](https://www.bilibili.com/video/BV1d3h5zFEjL?spm_id_from=333.788.videopod.sections&vd_source=cb2ffbc722372d15094f9eebc2c1e0a4)
