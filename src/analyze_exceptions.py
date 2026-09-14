from read_exceptions import load_exceptions

exceptions_df = load_exceptions()

#.shape() returns (rows, columns)
print("Shape:", exceptions_df.shape)


print("\nColumns:")
print(exceptions_df.columns)

# .value_counts() - counts how often each value occurs.
print("\nExceptions by Severity:")
print(exceptions_df["severity"].value_counts())

# .value_counts() - Which reconciliation rules are generating the most exceptions
print("\nExceptions by Rule:")
print(exceptions_df["rule_code"].value_counts())


# Answers some questions like - 
# 1. How serious are the currently detected reconciliation exceptions? (High, critical, medium, etc)
# 2. Which reconciliation problems occur most frequently?