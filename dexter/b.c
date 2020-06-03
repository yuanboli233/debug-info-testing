int main(){
    int a = 1;
    int b = 1;
    b++;
    return a + b;
}
//DexExpectWatchValue('b', '2', on_line=5)
