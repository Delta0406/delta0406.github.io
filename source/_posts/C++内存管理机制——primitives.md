---
title: C++内存管理机制——primitives
date: 2025-10-19 22:27:04
tags: 内存管理
categories: c++基础
---

# 内存分配的每个层面
C++的内存管理方式有如下四种，一般不直接使用操作系统的API进行管理，以尽可能避免与特定操作系统绑定。
![四种内存分配方式](./images/内存管理/四种内存分配方式.png)

四种内存操作方法的特性如下：
![四种内存分配方法特性](./images/内存管理/四种内存分配方法特性.png)

# new/detele expression
## 内存申请
通过new进行内存申请的过程：
1. 通过operator new()操作分配一个目标类型大小的内存，图中为Complex的大小。
2. 通过static_cast将得到的内存块强制转化为目标类型指针，这里是Complex*。
3. 调用目标类型的构造方法（注意：直接通过pc->Complex::Complex(1,2)这样的方法调用构造函数只有编译器可以做，用户这样做将产生错误）。
> operator new()操作的内部调用了malloc()函数
![new expression](./images/内存管理/new_expression.png)

## 内存释放
通过delete进行内存释放的过程：
1. 调用对象的析构函数
2. 通过operator delete释放内存，其内部使用的是free()函数
![delete expression](./images/内存管理/delete_expression.png)

# Array new
array new内存分配的过程：
1. 编译器分配一块内存，内存的首部cookie记录了对象内存分配的信息，首部后面紧跟着3个连续的对象内存
2. 为每个对象内存调用构造函数
![array new](./images/内存管理/array_new.png)
释放内存时，需要使用delete[]。如果使用delete，则只会调用第一个对象的析构函数，不会调用所有对象的析构函数。上图中的`new string[3]`是一个例子，只使用delete，将会导致只调用str[0]的析构函数，str[1]、str[2]的析构函数不会被调用，此时就会出现问题。

数组对象的创建与析构过程如下：
![array new & array delete](./images/内存管理/array_new&array_delete.png)
> 构造函数调用顺序是按照构建对象来的，但是析构函数执行是按照相反的顺序。

# placement new
placement new的语法为：
```c++
new (address) Type(constructor_args...);
```
表示在address这块已有的内存上调用Type的构造函数。示例如下：
![placement_new](./images/内存管理/placement_new.png)
> 没有placement delete，因为placement new没有分配新内存。

# 重载
## C++内存分配的途径
C++内存分配的途径如下图所示，没有重载会走路线二。如果类中重载了operator new()，那么会走路线一。但最终都会调用系统的::operator new()函数。
![c++内存分配的途径](./images/内存管理/cpp_memory_allocation_ways.png)

容器中的内存分配途径如下图所示，容器通过std::allocator实现内存的分配与回收，最终也是调用的::operator new()函数。
![容器内存分配途径](./images/内存管理/container_memory_allocation_ways.png)

## 重载new和delete
### 重载::operator new/::operator delete
使用内联函数重载::operator new和::operator delete：
![重载::operator new/::operator delete](./images/内存管理/global_operator_new_override.png)

### 重载operator new/operator delete
如果是在类中重载operator new()方法，该方法可以有多种形式，但是函数参数列表第一个参数必须是size_t类型变量。对于operator delete()，第一个参数必须是void*类型，第二参数size_t是可选项，可以去掉。
![重载operator new/operator delete](./images/内存管理/local_operator_new_override.png)

### 重载operator new[]/operator delete[]
![重载operator new[]/operator delete[]](./images/内存管理/local_operator_new_array_override.png)

## 测试案例
### 测试一
```c++
#include <cstddef>
#include <iostream>
#include <string>
using namespace std;

namespace jj06
{

	class Foo
	{
	public:
		int _id;
		long _data;
		string _str;

	public:
		static void* operator new(size_t size);
		static void  operator delete(void* deadObject, size_t size);
		static void* operator new[](size_t size);
		static void  operator delete[](void* deadObject, size_t size);

		Foo() : _id(0)      { cout << "default ctor. this=" << this << " id=" << _id << endl; }
		Foo(int i) : _id(i) { cout << "ctor. this=" << this << " id=" << _id << endl; }
		//virtual 
		~Foo()              { cout << "dtor. this=" << this << " id=" << _id << endl; }

		//不加 virtual dtor, sizeof = 12, new Foo[5] => operator new[]() 的 size 參數是 64, 
		//加了 virtual dtor, sizeof = 16, new Foo[5] => operator new[]() 的 size 參數是 84, 
		//上述二例，多出來的 4 可能就是個 size_t 欄位用來放置 array size. 
	};

	void* Foo::operator new(size_t size)
	{
		Foo* p = (Foo*)malloc(size);
		cout << "Foo::operator new(), size=" << size << "\t  return: " << p << endl;

		return p;
	}

	void Foo::operator delete(void* pdead, size_t size)
	{
		cout << "Foo::operator delete(), pdead= " << pdead << "  size= " << size << endl;
		free(pdead);
	}

	void* Foo::operator new[](size_t size)
	{
		Foo* p = (Foo*)malloc(size);  //crash, 問題可能出在這兒 
		cout << "Foo::operator new[](), size=" << size << "\t  return: " << p << endl;

		return p;
	}

	void Foo::operator delete[](void* pdead, size_t size)
	{
		cout << "Foo::operator delete[](), pdead= " << pdead << "  size= " << size << endl;

		free(pdead);
	}

	//-------------	
	void test_overload_operator_new_and_array_new()
	{
		cout << "\ntest_overload_operator_new_and_array_new().......... \n";

		cout << "sizeof(Foo)= " << sizeof(Foo) << endl;

		{
			Foo* p = new Foo(7);
			delete p;

			Foo* pArray = new Foo[5];	//無法給 array elements 以 initializer 
			delete[] pArray;
		}

		{
			cout << "testing global expression ::new and ::new[] \n";
			// 這會繞過 overloaded new(), delete(), new[](), delete[]() 
			// 但當然 ctor, dtor 都會被正常呼叫.  

			Foo* p = ::new Foo(7);
			::delete p;

			Foo* pArray = ::new Foo[5];
			::delete[] pArray;
		}
	}
} //namespace

int main(void)
{
	jj06::test_overload_operator_new_and_array_new();
	return 0;
}
```

### 测试二
```c++
#include <vector>  //for test
#include <cstddef>
#include <iostream>
#include <string>
using namespace std;

namespace jj07
{

	class Bad { };
	class Foo
	{
	public:
		Foo() { cout << "Foo::Foo()" << endl; }
		Foo(int) {
			cout << "Foo::Foo(int)" << endl;
			// throw Bad();  
		}

		//(1) 這個就是一般的 operator new() 的重載 
		void* operator new(size_t size){
			cout << "operator new(size_t size), size= " << size << endl;
			return malloc(size);
		}

		//(2) 這個就是標準庫已經提供的 placement new() 的重載 (形式)
		//    (所以我也模擬 standard placement new 的動作, just return ptr) 
		void* operator new(size_t size, void* start){
			cout << "operator new(size_t size, void* start), size= " << size << "  start= " << start << endl;
			return start;
		}

		//(3) 這個才是嶄新的 placement new 
		void* operator new(size_t size, long extra){
			cout << "operator new(size_t size, long extra)  " << size << ' ' << extra << endl;
			return malloc(size + extra);
		}

		//(4) 這又是一個 placement new 
		void* operator new(size_t size, long extra, char init){
			cout << "operator new(size_t size, long extra, char init)  " << size << ' ' << extra << ' ' << init << endl;
			return malloc(size + extra);
		}

		//(5) 這又是一個 placement new, 但故意寫錯第一參數的 type (它必須是 size_t 以滿足正常的 operator new) 
		//!  	void* operator new(long extra, char init) { //[Error] 'operator new' takes type 'size_t' ('unsigned int') as first parameter [-fpermissive]
		//!	  	cout << "op-new(long,char)" << endl;
		//!    	return malloc(extra);
		//!  	} 	

		//以下是搭配上述 placement new 的各個 called placement delete. 
		//當 ctor 發出異常，這兒對應的 operator (placement) delete 就會被喚起. 
		//應該是要負責釋放其搭檔兄弟 (placement new) 分配所得的 memory.  
		//(1) 這個就是一般的 operator delete() 的重載 
		void operator delete(void*, size_t)
		{
			cout << "operator delete(void*,size_t)  " << endl;
		}

		//(2) 這是對應上述的 (2)  
		void operator delete(void*, void*)
		{
			cout << "operator delete(void*,void*)  " << endl;
		}

		//(3) 這是對應上述的 (3)  
		void operator delete(void*, long)
		{
			cout << "operator delete(void*,long)  " << endl;
		}

		//(4) 這是對應上述的 (4)  
		//如果沒有一一對應, 也不會有任何編譯報錯 
		void operator delete(void*, long, char)
		{
			cout << "operator delete(void*,long,char)  " << endl;
		}

	private:
		int m_i;
	};


	//-------------	
	void test_overload_placement_new()
	{
		cout << "\n\n\ntest_overload_placement_new().......... \n";

		Foo start;  //Foo::Foo

		Foo* p1 = new Foo;           //op-new(size_t)
		Foo* p2 = new (&start) Foo;  //op-new(size_t,void*)
		Foo* p3 = new (100) Foo;     //op-new(size_t,long)
		Foo* p4 = new (100, 'a') Foo; //op-new(size_t,long,char)

		Foo* p5 = new (100) Foo(1);     //op-new(size_t,long)  op-del(void*,long)
		Foo* p6 = new (100, 'a') Foo(1); //
		Foo* p7 = new (&start) Foo(1);  //
		Foo* p8 = new Foo(1);           //
		//VC6 warning C4291: 'void *__cdecl Foo::operator new(unsigned int)'
		//no matching operator delete found; memory will not be freed if
		//initialization throws an exception
	}
} //namespace	

int main(void)
{
	jj07::test_overload_placement_new();
	return 0;
}
```

# pre-class allocator
为每个类设计内存管理工具。
## 示例1
![per-class-allocator1](./images/内存管理/per-class-allocator1.png)
测试：
![per-class-allocator1-test](./images/内存管理/per-class-allocator1-test.png)
代码：
```c++
#include <cstddef>
#include <iostream>
using namespace std;

namespace jj04
{
	//ref. C++Primer 3/e, p.765
	//per-class allocator 

	class Screen {
	public:
		Screen(int x) : i(x) { };
		int get() { return i; }

		void* operator new(size_t);
		void  operator delete(void*, size_t);	//(2)
		//! void  operator delete(void*);			//(1) 二擇一. 若(1)(2)並存,會有很奇怪的報錯 (摸不著頭緒) 

	private:
		Screen* next;
		static Screen* freeStore;
		static const int screenChunk;
	private:
		int i;
	};
	Screen* Screen::freeStore = 0;
	const int Screen::screenChunk = 24;

	void* Screen::operator new(size_t size)
	{
		Screen *p;
		if (!freeStore) {
			//linked list 是空的，所以攫取一大塊 memory
			//以下呼叫的是 global operator new
			size_t chunk = screenChunk * size;
			freeStore = p =
				reinterpret_cast<Screen*>(new char[chunk]);
			//將分配得來的一大塊 memory 當做 linked list 般小塊小塊串接起來
			for (; p != &freeStore[screenChunk - 1]; ++p)
				p->next = p + 1;
			p->next = 0;
		}
		p = freeStore;
		freeStore = freeStore->next;
		return p;
	}


	//! void Screen::operator delete(void *p)		//(1)
	void Screen::operator delete(void *p, size_t)	//(2)二擇一 
	{
		//將 deleted object 收回插入 free list 前端
		(static_cast<Screen*>(p))->next = freeStore;
		freeStore = static_cast<Screen*>(p);
	}

	//-------------
	void test_per_class_allocator_1()
	{
		cout << "\ntest_per_class_allocator_1().......... \n";

		cout << sizeof(Screen) << endl;		//8	

		size_t const N = 100;
		Screen* p[N];

		for (int i = 0; i< N; ++i)
			p[i] = new Screen(i);

		//輸出前 10 個 pointers, 用以比較其間隔 
		for (int i = 0; i< 10; ++i)
			cout << p[i] << endl;

		for (int i = 0; i< N; ++i)
			delete p[i];
	}
} //namespace

int main(void)
{
	jj04::test_per_class_allocator_1();
	return 0;
}
```
> 内存池本质上是分配了一大块内存，然后将该内存分割为多个小块通过链表拼接起来，所以物理上不一定连续，但是逻辑上是连续的。

## 示例2
![per-class-allocator2](./images/内存管理/per-class-allocator2.png)
测试：
![per-class-allocator2-test](./images/内存管理/per-class-allocator2-test.png)
代码：
```c++
#include <cstddef>
#include <iostream>
using namespace std;

namespace jj05
{
	//ref. Effective C++ 2e, item10
	//per-class allocator 

	class Airplane {   //支援 customized memory management
	private:
		struct AirplaneRep {
			unsigned long miles;
			char type;
		};
	private:
		union {
			AirplaneRep rep;  //此針對 used object
			Airplane* next;   //此針對 free list
		};
	public:
		unsigned long getMiles() { return rep.miles; }
		char getType() { return rep.type; }
		void set(unsigned long m, char t)
		{
			rep.miles = m;
			rep.type = t;
		}
	public:
		static void* operator new(size_t size);
		static void  operator delete(void* deadObject, size_t size);
	private:
		static const int BLOCK_SIZE;
		static Airplane* headOfFreeList;
	};

	Airplane* Airplane::headOfFreeList;
	const int Airplane::BLOCK_SIZE = 512;

	void* Airplane::operator new(size_t size)
	{
		//如果大小錯誤，轉交給 ::operator new()
		if (size != sizeof(Airplane))
		return ::operator new(size);

		Airplane* p = headOfFreeList;

		//如果 p 有效，就把list頭部移往下一個元素
		if (p)
			headOfFreeList = p->next;
		else {
			//free list 已空。配置一塊夠大記憶體，
			//令足夠容納 BLOCK_SIZE 個 Airplanes
			Airplane* newBlock = static_cast<Airplane*>
				(::operator new(BLOCK_SIZE * sizeof(Airplane)));
			//組成一個新的 free list：將小區塊串在一起，但跳過 
			//#0 元素，因為要將它傳回給呼叫者。
			for (int i = 1; i < BLOCK_SIZE - 1; ++i)
				newBlock[i].next = &newBlock[i + 1];
			newBlock[BLOCK_SIZE - 1].next = 0; //以null結束

			// 將 p 設至頭部，將 headOfFreeList 設至
			// 下一個可被運用的小區塊。
			p = newBlock;
			headOfFreeList = &newBlock[1];
		}
		return p;
	}

	// operator delete 接獲一塊記憶體。
	// 如果它的大小正確，就把它加到 free list 的前端
	void Airplane::operator delete(void* deadObject,
		size_t size)
	{
		if (deadObject == 0) return;
		if (size != sizeof(Airplane)) {
			::operator delete(deadObject);
			return;
		}

		Airplane *carcass =
			static_cast<Airplane*>(deadObject);

		carcass->next = headOfFreeList;
		headOfFreeList = carcass;
	}

	//-------------
	void test_per_class_allocator_2()
	{
		cout << "\ntest_per_class_allocator_2().......... \n";

		cout << sizeof(Airplane) << endl;    //8

		size_t const N = 100;
		Airplane* p[N];

		for (int i = 0; i< N; ++i)
			p[i] = new Airplane;


		//隨機測試 object 正常否 
		p[1]->set(1000, 'A');
		p[5]->set(2000, 'B');
		p[9]->set(500000, 'C');
		cout << p[1] << ' ' << p[1]->getType() << ' ' << p[1]->getMiles() << endl;
		cout << p[5] << ' ' << p[5]->getType() << ' ' << p[5]->getMiles() << endl;
		cout << p[9] << ' ' << p[9]->getType() << ' ' << p[9]->getMiles() << endl;

		//輸出前 10 個 pointers, 用以比較其間隔 
		for (int i = 0; i< 10; ++i)
			cout << p[i] << endl;

		for (int i = 0; i< N; ++i)
			delete p[i];
	}
} //namespace

int main(void)
{
	jj05::test_per_class_allocator_2();
	return 0;
}
```
> union(联合体):所有成员共享同一块内存，大小=最大成员大小（加上可能的补充）
> 使用union保存链表元素的next指针，这样可以节省空间。delete时，没有直接删除目标元素，而是将它作为下一个可以分配的内存空间。 

# static allocator
![static-allocator1](./images/内存管理/static-allocator1.png)
![static-allocator2](./images/内存管理/static-allocator2.png)
![static-allocator-result](./images/内存管理/static-allocator-result.png)
代码：
```c++
#include <cstddef>
#include <iostream>
#include <complex>
using namespace std;

namespace jj09
{

	class allocator
	{
	private:
		struct obj {
			struct obj* next;  //embedded pointer
		};
	public:
		void* allocate(size_t);
		void  deallocate(void*, size_t);
		void  check();

	private:
		obj* freeStore = nullptr;
		const int CHUNK = 5; //小一點方便觀察 
	};

	void* allocator::allocate(size_t size)
	{
		obj* p;

		if (!freeStore) {
			//linked list 是空的，所以攫取一大塊 memory
			size_t chunk = CHUNK * size;
			freeStore = p = (obj*)malloc(chunk);

			//cout << "empty. malloc: " << chunk << "  " << p << endl;

			//將分配得來的一大塊當做 linked list 般小塊小塊串接起來
			for (int i = 0; i < (CHUNK - 1); ++i)	{  //沒寫很漂亮, 不是重點無所謂.  
				p->next = (obj*)((char*)p + size);
				p = p->next;
			}
			p->next = nullptr;  //last       
		}
		p = freeStore;
		freeStore = freeStore->next;

		//cout << "p= " << p << "  freeStore= " << freeStore << endl;

		return p;
	}
	void allocator::deallocate(void* p, size_t)
	{
		//將 deleted object 收回插入 free list 前端
		((obj*)p)->next = freeStore;
		freeStore = (obj*)p;
	}
	void allocator::check()
	{
		obj* p = freeStore;
		int count = 0;

		while (p) {
			cout << p << endl;
			p = p->next;
			count++;
		}
		cout << count << endl;
	}
	//--------------

	class Foo {
	public:
		long L;
		string str;
		static allocator myAlloc;
	public:
		Foo(long l) : L(l) {  }
		static void* operator new(size_t size)
		{ return myAlloc.allocate(size); }
		static void  operator delete(void* pdead, size_t size)
		{
			return myAlloc.deallocate(pdead, size);
		}
	};
	allocator Foo::myAlloc;


	class Goo {
	public:
		complex<double> c;
		string str;
		static allocator myAlloc;
	public:
		Goo(const complex<double>& x) : c(x) {  }
		static void* operator new(size_t size)
		{ return myAlloc.allocate(size); }
		static void  operator delete(void* pdead, size_t size)
		{
			return myAlloc.deallocate(pdead, size);
		}
	};
	allocator Goo::myAlloc;

	//-------------	
	void test_static_allocator_3()
	{
		cout << "\n\n\ntest_static_allocator().......... \n";

		{
			Foo* p[100];

			cout << "sizeof(Foo)= " << sizeof(Foo) << endl;
			for (int i = 0; i<23; ++i) {	//23,任意數, 隨意看看結果 
				p[i] = new Foo(i);
				cout << p[i] << ' ' << p[i]->L << endl;
			}
			//Foo::myAlloc.check();

			for (int i = 0; i<23; ++i) {
				delete p[i];
			}
			//Foo::myAlloc.check();
		}

		{
			Goo* p[100];

			cout << "sizeof(Goo)= " << sizeof(Goo) << endl;
			for (int i = 0; i<17; ++i) {	//17,任意數, 隨意看看結果 
				p[i] = new Goo(complex<double>(i, i));
				cout << p[i] << ' ' << p[i]->c << endl;
			}
			//Goo::myAlloc.check();

			for (int i = 0; i<17; ++i) {
				delete p[i];
			}
			//Goo::myAlloc.check();	
		}
	}
} //namespace	

int main(void)
{
	jj09::test_static_allocator_3();
	return 0;
}
```

![macro-static-allocate](./images/内存管理/macro-static-allocate.png)
![macro-static-allocate-result](./images/内存管理/macro-static-allocate-result.png)

# global allocator
上面自定义的分配器使用一条链表来管理内存，而标准库却用了多条链表来进行管理：
![global_allocator](./images/内存管理/global_allocator.png)

# new handler
如果用户申请内存时，因为系统原因或申请内存过大导致失败，这是将抛出异常。operator new()函数内部将会调用_calnewh()函数，这个函数通过左边的typedef传入，可以根据需要自己编写handler处理函数来处理该问题。一般有两种方案处理：
* 让更多的Memory可用
* 直接abort()或exit()
![def_new_handler](./images/内存管理/def_new_handler.png)
![new_handler](./images/内存管理/new_handler.png)

# =default和=delete
有默认版本的函数有：
* 拷贝构造函数
* 拷贝赋值函数
* 析构函数
![default_delete1](./images/内存管理/default_delete1.png)
![default_delete2](./images/内存管理/defualt_delete2.png)

# 参考
[CPP-Memory-Management](https://github.com/hujiese/CPP-Memory-Management/tree/master)
[侯捷-C++内存管理机制](https://www.bilibili.com/video/BV1d3h5zFEjL?spm_id_from=333.788.videopod.sections&vd_source=cb2ffbc722372d15094f9eebc2c1e0a4)


