def factorial(n: int) -> int:
    """计算正整数的阶乘"""
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

if __name__ == "__main__":
    num = int(input("请输入一个正整数计算阶乘: "))
    print(f"恭喜！{num} 的阶乘是: {factorial(num)}")