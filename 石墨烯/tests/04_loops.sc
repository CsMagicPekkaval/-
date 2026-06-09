int main() {
  int i;
  int sum;
  sum = 0;
  for (i = 1; i <= 5; i = i + 1) {
    sum += i;
  }
  printf("%d\n", sum);
  i = 0;
  do {
    i++;
  } while (i < 3);
  printf("%d\n", i);
  return 0;
}
