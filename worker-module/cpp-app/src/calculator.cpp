// C++ program to find the prime numbers
// between a given interval
#include <bits/stdc++.h>
#include <iostream>
#include <stdio.h>
#include <cstdlib>

using namespace std;
 
// Function for finding prime numbers in given range
void primeInRange(int L, int R)
{
    int flag;
 
    // Traverse each number in the
    // interval with the help of for loop
    for (int i = L; i <= R; i++) {
 
        // Skip 0 and 1 as they are
        // neither prime nor composite
        if (i == 1 || i == 0)
            continue;
 
        // flag variable to tell
        // if i is prime or not
        flag = 1;
 
        // Iterate to check if i is prime
        // or not
        for (int j = 2; j <= i / 2; ++j) {
            if (i % j == 0) {
                flag = 0;
                break;
            }
        }
 
        // flag = 1 means i is prime
        // and flag = 0 means i is not prime
        if (flag == 1)
            cout << i << " ";
    }
}

// Function for finding fibonacci numbers in given range
void FibonacciSequence(int L, int R)
{
int a = 0, b = 1, c = 0;
    while (c <= R) {
        if (c >= L) {
            std::cout << c << " ";
        }
        c = a + b;
        a = b;
        b = c;
    }
}
 



// Entrypoint
int main(int argc, char *argv[])
{
    // Get params
    std::string function = argv[1];
    int L = atoi(argv[2]);
    int R = atoi(argv[3]);

    if(argc != 4){
	printf("/nIncorrect arguments - please provide start and end search range /n");

    }else if (argc == 4 && function =="prime" ){
      	printf("\n*** CALCULATING PRIMES BETWEEN %d AND %d **\n" , L , R);

    	// Prime function Call
    	primeInRange(L, R);
 
    	printf("\n*** PRIME CALCULATION COMPLETE ***\n\n");

    }else if (argc == 4 && function =="prime" ){
      	printf("\n*** CALCULATING FIBONACCI NUMBERS BETWEEN %d AND %d **\n" , L , R);

    	// Prime function Call
    	FibonacciSequence(L, R);
 
    	printf("\n*** FIBONACCI CALCULATION COMPLETE ***\n\n");

    } else {
        printf("\nFunction not defined and task will be ignored...\n\n");
    }

    return 0;
}
