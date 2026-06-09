void swap(int *a, int *b) {
  int temp;
  temp = *a;
  *a = *b;
  *b = temp;
}

void bubble_sort(int *arr, int n) {
  int i;
  int j;
  for (i = 0; i < n - 1; i = i + 1) {
    for (j = 0; j < n - 1 - i; j = j + 1) {
      if (arr[j] > arr[j + 1]) {
        swap(&arr[j], &arr[j + 1]);
      }
    }
  }
}

void print_array(int *arr, int n) {
  int i;
  for (i = 0; i < n; i = i + 1) {
    printf("%d ", arr[i]);
  }
  printf("\n");
}

int main() {
  int data[8];
  data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;
  data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 31;
  printf("Before sorting: ");
  print_array(data, 8);
  bubble_sort(data, 8);
  printf("After sorting: ");
  print_array(data, 8);
  return 0;
}
