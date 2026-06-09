int main() {
  int x;
  int *p;
  x = 42;
  p = &x;
  printf("%d\n", *p);
  *p = 99;
  printf("%d\n", x);
  return 0;
}
