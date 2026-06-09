int main() {
  int arr[5];
  int i;
  for (i = 0; i < 5; i = i + 1) {
    arr[i] = (i + 1) * 10;
  }
  printf("%d %d %d\n", arr[0], arr[2], arr[4]);
  return 0;
}
