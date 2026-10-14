# In the term of new metric success rate over time we can see that PACT has the highest success rate over time, followed by ICIO and RTF. This indicates that PACT
# is the most efficient method in terms of achieving successful outcomes within a given time frame.
# Even though ICIO has a higher success rate in percentages, when we consider the time taken to achieve those successes, RFT proves to be more effective.
time = {'ICIO': 170.0,
        'PACT': 131.0,
        'RTF': 138.0,}

steps = {'ICIO': 26,
         'PACT': 31, 
        'RTF': 25,}

#in percentages
success_rate = {     
        'ICIO':27.74,
        'PACT': 27.74,
        'RTF': 25.16,
}

def succes_rate_over_Time():
    success_rate_over_time = {}
    #success rate over time = success rate (percentages) / (time in hours)
    for method in time.keys():
        success_rate_over_time[method] = success_rate[method] / (time[method] / 3600)  
    return success_rate_over_time

def print_metrics():
    success_rate = succes_rate_over_Time()
    print("Success Rate over Time:")
    for method, rate in success_rate.items():
        print(f"{method}: {rate:.4f} success rate over hour")
        print(f" {method} Steps taken: {steps[method]}")
        print(f" {method} Time taken: {time[method]} seconds")

if __name__ == "__main__":
    print_metrics()
