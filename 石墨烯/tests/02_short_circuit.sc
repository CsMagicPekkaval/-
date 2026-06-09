int main() {
  int x;
  x = 0;
  printf("%d\n", x && (10 / x));
  printf("%d\n", 1 || (10 / x));
  printf("%d\n", (x == 0) && 1);
  return 0;
}
