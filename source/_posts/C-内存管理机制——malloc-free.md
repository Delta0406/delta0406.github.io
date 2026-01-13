---
title: C++内存管理机制——malloc_free
date: 2025-11-13 21:29:05
tags: 内存管理
categories: c++基础
---

# VC6 VS VC10
## VC6内存分配
下面的图片展示了VC6内存分配的调用栈，操作系统会调用`mainCRTStartup()`做一些准备工作，然后才会调用程序编写者的`main()`函数。在`_heap_alloc_base()`函数中，如果申请的内存大小小于`_shb_threshold`，则会通过`_sbh_alloc_block(size)`申请内存，否则通过操作系统的`HeapAlloc()`申请内存。
> SBH: Small Block Heap

![VC6内存分配调用栈](./images/内存管理/暂存/内存管理_98.jpg)

## VC10内存分配
VC10则无论什么大小，都通过系统的`HeapAlloc()`来申请内存。这是否意味着VC6的设计没有意义了呢？并不是，只是这些操作由操作系统来完成了。

![VC10内存分配调用栈](./images/内存管理/暂存/内存管理_99.jpg)

## SBH之始——`_heap_init()`和`_sbh_heap_init()`
`_heap_init()`是crt的第一个动作，它会通过`HeapCreate()`向操作系统申请一块大内存，接着，调用`_sbh_heap_init()`进行初始化，从之前分配的`_crtheap`中申请16个`HEADER`大小的内存空间。

![_heap_init()和_sbh_heap_init()](./images/内存管理/暂存/内存管理_100.jpg)
![HEADER结构](./images/内存管理/暂存/内存管理_101.jpg)

# VC6内存管理
## _ioinit()
### _malloc_crt()
`_ioinit()`内部调用`_malloc_crt(IOINFO_ARRAY_ELTS * sizeof(ioinfo))`分配内存。如果当前不是`_DEBUG`模式，则`_malloc_crt`就对应`malloc`，否则对应`_malloc_dbg`。申请的这块内存大小为`32*8=256`（`IOINFO_ARRAY_ELTS`是32，`ioinfo`结构体本身是6，但会被对齐到8），在16进制时表示为`100`。

![_ioinit()](./images/内存管理/暂存/内存管理_102.jpg)

### _heap_alloc_dbg()
`_heap_alloc_dbg()`则会在分配内存的基础上添加debug信息构建内存块，内存块的结构如下图所示。每个内存块的大小为`sizeof(_CrtMemBlockHeader)+nSize+nNoMansLandSize`。header部分是`_CrtMemBlockHeader`，包含指向上一个内存块和下一个内存块的指针，调用方的文件名，调用的代码行、申请的内存大小等debug信息。`nSize`是申请的内存大小，即上一小节提到的`256`。申请内存区域上下被无人区`nNoMansLandSize`包围，无人区写入的内容是固定的，用于判断是否越界。

![_heap_alloc_dbg()1](./images/内存管理/暂存/内存管理_103.jpg)
![_heap_alloc_dbg()2](./images/内存管理/暂存/内存管理_104.jpg)

### _heap_alloc_base()
这里会对申请内存大小做一次判断，如果小于等于`__sbh_threshold`，则调用`_sbh_alloc_block(size)`分配内存。否则，通过操作系统的`HeapAlloc()`申请内存。`__sbh_threshold`的值为1016，因为此时的size还不是完整内存块的大小，后续还会加上`cookie`，而我们知道`cookie`的大小为8。

![_heap_alloc_base()](./images/内存管理/暂存/内存管理_105.jpg)

### __sbh_alloc_block()
到这个阶段，才开始为内存块加上`cookie`，并通过`BYTES_PER_PARA`做16字节的对齐。

![__sbh_alloc_block()](./images/内存管理/暂存/内存管理_106.jpg)

### __sbh_alloc_new_region()
一个`header`将会申请真正的内存，并在将来分割出去。分割出来的块有大有小，为了对其做管理。会`new`出来一块`region`，`region`中有32个`group`，每个`group`是大小为64的双向链表。`BITVEC`是`unsigned integer`，`region`中有32组`bitvGroup`，一组是64位（32+32）。

![__sbh_alloc_new_region](./images/内存管理/暂存/内存管理_107.jpg)

### __shb_alloc_new_group()
对于申请到的1MB的大内存块，将其分为32个`group`，每个`group`大小为`1024/32=32K`。每个`group`还可以细分为8块，每块大小为`4k`，称之为`page`。单个`page`中用两块存放内容为`0xfffffff`的内存标记包含的区域，图中4080是两块`0xffffffff`中间的区域大小，而两块`0xffffffff`是8个字节，`4096-8=4088`，为了做16个字节的对齐，将其中8位留作保留位，剩下的4080供使用。

![__sbh_alloc_new_group()](./images/内存管理/暂存/内存管理_108.jpg)

当前阶段是初始化阶段，8个`page`是直接由`group`链表中的最后一组来管理的，这组链表用来管理超过`1k`的内存。
![__sbh_alloc_new_group()_page](./images/内存管理/暂存/内存管理_109.jpg)

### 切割
`_ioinit()`申请了256（16进制表示为100）字节的内存，加上debug信息和`cookie`，共计`130`字节。`crt`会根据需求申请对应的内存块，并向其中写入debug信息，其中`00000002`是`nBlockUse`的值，表示这是`_CRT_BLOCK`，main函数结束前应检查`_NORMAL_BLOCK`是否还有使用的，而不是所有`BLOCK`。系统会返回实际可填充的`fill 0xcd`的地址给调用方。

![切割](./images/内存管理/暂存/内存管理_110.jpg)

## SBH行为分析
### 首次分配
首次分配是为`_ioinit()`进行分配，申请的内存大小为`100h`，加上debug信息和`cookie`后，共计`130h`，`130h`在`header`中对应编号为18的链表（链表对应的内存块大小为`19*16=304`，`(304+15)/16-1=18`）。最开始初始化的时候，已经有16个`HEADER`了，编号为0的`HEADER`会开始处理，使用`p=VirtualAlloc(0, 1Mb, MEM_RESERVE,...)`申请1Mb的内存，这里的内存是虚拟内存，0表示不指定位置，`MEM_RESERVE`表示保留地址空间。接着，使用`HeapAlloc(crtheap, sizeof(REGION))`分配`Region`所需的内存，包括其管理的`Group`。`Group0`指向一个大小为64的链表，然后从1Mb的预备内存中获取32k的内存，其中有8个`page`。用指针将`page`串起来，用`Group0`管理链表的最后一对指针进行管理（前面提到过`page`大小超过1k，使用最后一堆指针进行管理）。这32k的内存是通过`VirtualAlloc(addr, 32Kb, MEM_COMMIT,...)`获取的，其中`MEM_COMMIT`表示真的分配物理内存。接下来在`page1`中为调用方分配内存，并返回可填充的地址。`Region`中的`bitvGroup`共有32组，对应着`Group`中的64个链表，哪一条链表有区块哪一条对应的bit就被置为1，因此只有最后一位bit被置为1。因为`Group0`当前正在被使用，因此`indGroupUse`值为0。

![SBH行为分析——首次分配](./images/内存管理/暂存/内存管理_111.jpg)

### 第2次及第3次，分配
第二次分配是为`_crtGetEnvironmentStringA`分配内存，该内存的大小由设置的环境变量决定，图中示例为加上debug等信息后240。`240h=256*2+4*16=576`，`(576+15)/16-1=35`，因此去`bitvGroup`中查询第35号链表是否已经分配了。没有分配，能够找到最近的已经分配的是最后一个链表，因此去最后一个链表中分配内存。

![SBH行为分析——第2次，分配](./images/内存管理/暂存/内存管理_112.jpg)
![SBH行为分析——第3次，分配](./images/内存管理/暂存/内存管理_113.jpg)

### 第15次，释放
假设第15次进行释放操作，此时会先归还`_crtGetEnvironmentStringA`得到的240h的内存，因为这个节点已经处理完环境变量了，在没有执行`main()`之前就会归还这部分内存。

`240h/10h`结果是十进位的36，因此会归还到编号为35的链表。内存两端的`0x00000241`会被修改为`0x00000240`，表示这块内存已经被free了。并将内存块从数据转变成嵌入式指针，由35号链表进行管理，35号链表对应的bit位被置为1。 前14次都是分配，`cntEntries`值为14，此时也要减1变成13。

![SBH行为分析——第15次，释放](./images/内存管理/暂存/内存管理_114.jpg)

### 第16次，分配
第16次，申请`b0`大小的内存。向右找到最近的已分配内存的链表——35号链表，为其分配内存，240h的内存还剩190h为空闲，`190h/10h=25`，因此应当放到编号为24的链表中管理。

![SBH行为分析——第16次，分配](./images/内存管理/暂存/内存管理_115.jpg)

### 第n次，分配
`Group0`内存使用情况用`02000014 00000000`表示。申请230h的内存，如恰好存在可以分配的链表则标志位应为`00000000 20000000`，因此`Group0`无法满足要求。开始使用`Group1`，`indGroupUse`值变更为1。
> 图中`00000000 20000000`中每个数字由4个二进制位组成，8个0就是`4*8=32`，2为`0010`，因此`00000000 20000000`就对应34号链表。

![SBH行为分析——第n次，分配](./images/内存管理/暂存/内存管理_116.jpg)

### 区块合并
下图展示了区块合并的过程，当前计划回收灰色的区块，其内存大小为300h。在将其回收时，`free(ptr)`中`ptr`应当指向的是可填充位置的首地址，可以通过读其上4个字节的`cookie`获取到这块内存的大小，然后加上内存大小跳转到下一块内存的`cookie`，检查下一块内存是否为空，如果是则将两块内存合并，直到下一个块内存不为空。接着，检查其上方的内存，如果为空则合并，直至不为空。将合并后的内存交由对应的链表进行管理。

![区块合并](./images/内存管理/暂存/内存管理_117.jpg)

## free(p)
`SBH`会维护一个`__sbh_pHeaderList`指向`Header`表格，而通过单个header可以找到对应的`1Mb`内存，可以直接计算地址是否在该内存中，通过这种方式我们可以定位到p在哪个`Header`内。至于`Group`，则通过`(p-Header)/32Kb`定位。定位所在的`free_list`则是通过读`cookie`知道自身内存大小，然后计算应该位于哪块`free_list`。

![free(p)](./images/内存管理/暂存/内存管理_118.jpg)

## 总结
1. 为什么要把内存分成这么多段，并且用`group`进行管理？
如果只用一个`group`进行管理，则切割成大大小小的块之后，则回收时需要全部为空才能回收，减小粒度之后更容易回收。

2. 如何判断全回收
通过`cntEntries`记录malloc和free的次数，malloc之后就加1，free之后就减1，这样就无需遍历链表，实现快速判断是否需要全回收。

![分段与全回收](./images/内存管理/暂存/内存管理_119.jpg)

3. 为什么8个`Page`都为空之后不进行合并再回收？
因为`SBH`不是立即回收，它会保留一段时间，等到下次全回收的时候再回收，这样可以减少向系统申请内存的开销。维持原有的链表结构，可以更快的利用内存。

4. 如何延缓全回收的动作？
在`__sbh_heap_init()`时将`__sbh_pHeaderScan`值置为NULL了，该指针指向一个全回收`Group`所属的`Header`，这个`Group`原本应该被释放，但暂时保留了。当有第二个全回收的`Group`时，才释放这个`Defer Group`，将新出现的全回收`Group`设为`Defer`。如果尚未出现第二个全回收而又从`Defer Group`中取出block完成分配，则`Defer`指针会被置为NULL，即该`Group`会再次投入使用，不会被全回收。`__sbh_indGroupDefer`是索引，指出`Region`中哪个`Group`是`Defer`。

![全回收策略](./images/内存管理/暂存/内存管理_120.jpg)

# 参考
[侯捷-C++内存管理机制](https://www.bilibili.com/video/BV1d3h5zFEjL?spm_id_from=333.788.videopod.sections&vd_source=cb2ffbc722372d15094f9eebc2c1e0a4)
