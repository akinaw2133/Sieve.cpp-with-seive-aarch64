#include<iostream>
using namespace std;
#ifdef _WIN32
#define USE_WINDOWS_TIMER
#endif

						 // number of primes between 2 and x:
						 //             10 =>           4
						 //            100 =>          25
						 //          1,000 =>         168
						 //         10,000 =>       1,229
						 //        100,000 =>       9,592
						 //      1,000,000 =>      78,498
						 //     10,000,000 =>     664,579
						 //    100,000,000 =>   5,761,455
						 //  1,000,000,000 =>  50,847,534
						 // 10,000,000,000 => 455,052,511

int lastNumber;
#include <stdio.h>
#include <math.h>
// simple serial sieve of Eratosthenes
int eratosthenes(int lastNumber)
{
	// initialize
	char* isPrime = new char[lastNumber + 1];
	for (int i = 0; i <= lastNumber; i++)
		isPrime[i] = 1;

	// find all non-primes
	for (int i = 2; i*i <= lastNumber; i++)
		if (isPrime[i])
			for (int j = i*i; j <= lastNumber; j += i)
				isPrime[j] = 0;

	// sieve is complete, count primes
	int found = 0;
	for (int i = 2; i <= lastNumber; i++)
		found += isPrime[i];

	delete[] isPrime;
	return found;
}

#ifdef USE_WINDOWS_TIMER
#include <windows.h>
#else
#include <sys/time.h>
#endif

double seconds()
{
#ifdef USE_WINDOWS_TIMER
	LARGE_INTEGER frequency, now;
	QueryPerformanceFrequency(&frequency);
	QueryPerformanceCounter(&now);
	return now.QuadPart / double(frequency.QuadPart);
#else
	timeval now;
	gettimeofday(&now, NULL);
	return now.tv_sec + now.tv_usec / 1000000.0;
#endif
}

int main(int argc, char *argv[])
{
	int lastnumber=100000000;
	printf("Primes between 2 and %d\n\n", lastnumber);
	printf("Simple Sieve\n");
	int startTime = seconds();
	int found = eratosthenes(lastnumber);
	double duration = seconds() - startTime;
	printf("--> %d primes found in %.3fs\n\n", found, duration);
	getchar();
	return 0;

}


