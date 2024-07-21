def calculate_pension(P, i, n, personal_account_balance, retirement_age):
    # 基础养老金 = (P + P * i) ÷ 2 × n × 1%
    basic_pension = P * (1 + i) / 2 * n * 0.01

    # 个人账户养老金 = 个人账户储存额 ÷ 计发月数
    if retirement_age == 50:
        months_to_calculate = 195
    elif retirement_age == 55:
        months_to_calculate = 170
    else:  # default to 60 years
        months_to_calculate = 139

    personal_account_pension = personal_account_balance / months_to_calculate

    # 过渡性养老金这里暂不计算, assuming it as 0
    transitional_pension = 0

    # 退休养老金 = 基础养老金 + 个人账户养老金 + 过渡性养老金
    total_pension = basic_pension + personal_account_pension + transitional_pension

    return {
        "basic_pension": basic_pension,
        "personal_account_pension": personal_account_pension,
        "total_pension": total_pension
    }


# 示例计算:
# - 当地上年度在岗职工月平均工资 (P) = 7000 元
# - 本人历年缴费指数的平均值 (i) = 0.6 (60%)
# - 本人累计缴费年限 (n) = 15 年
# - 个人账户储存额 = 72000 元
# - 退休年龄 = 60 岁

print(14873*(1+2.27)/2*15*0.01+33891*0.08*15*12/139)
