'''
Created on 12 Jun 2017

@author: cheng_feng
'''


import pandas as pd
import numpy as np
from sklearn import mixture
from sklearn.linear_model import Lasso
from sklearn import metrics
from AD import Util
import time

'parameters to tune'
eps = 0.01 #same as in the paper
sigma = 1.1 #buffer scaler
theta_value = 0.08 #same as in the paper
gamma_value = 0.9 #same as in the paper
max_k=4

'data preprocessing'
training_data,test_data = [],[]
for i in range(5):
    training_data.append(pd.read_csv("../data/SWaT_Dataset_Normal_Part"+str(i)+".csv"))
    test_data.append(pd.read_csv("../data/SWaT_Dataset_Attack_Part"+str(i)+".csv"))
training_data = pd.concat(training_data)
test_data = pd.concat(test_data)
training_data = training_data.reset_index(drop=True)
test_data = test_data.reset_index(drop=True)
 
 
 
 
'predicate generation'  
cont_vars = []
training_data = training_data.fillna(method='ffill')
test_data = test_data.fillna(method='ffill')
for entry in training_data:
    if training_data[entry].dtypes == np.float64:
        max_value = training_data[entry].max()
        min_value = training_data[entry].min()
        if max_value != min_value:
            training_data[entry + '_update'] = training_data[entry].shift(-1) - training_data[entry]
            test_data[entry + '_update'] = test_data[entry].shift(-1) - test_data[entry]            
            cont_vars.append(entry + '_update')
      
training_data = training_data[:len(training_data)-1]
test_data = test_data[:len(test_data)-1]
   
anomaly_entries = []
for entry in cont_vars:
    print('generate distribution-driven predicates for',entry)
    X = training_data[entry].values
    X = X.reshape(-1, 1)
    lowest_bic = np.infty
    bic = []
    n_components_range = range(1, 6)
    cluster_num = 0
    for n_components in n_components_range:
        # Fit a Gaussian mixture with EM
        gmm = mixture.GaussianMixture(n_components=n_components)
        gmm.fit(X)
        bic.append(gmm.bic(X))
        if bic[-1] < lowest_bic:
            lowest_bic = bic[-1]
            clf = gmm
            cluster_num = n_components
          
    Y = clf.predict(X)
    training_data[entry+'_cluster'] = Y
    cluster_num = len(training_data[entry+'_cluster'].unique() )
    scores = clf.score_samples(X)
    score_threshold = scores.min()*sigma
          
    test_X = test_data[entry].values
    test_X = test_X.reshape(-1, 1)
    test_Y = clf.predict(test_X)
    test_data[entry+'_cluster'] = test_Y
    test_scores = clf.score_samples(test_X)
    test_data.loc[test_scores<score_threshold,entry+'_cluster']=cluster_num
    if len(test_data.loc[test_data[entry+'_cluster']==cluster_num,:])>0:
        anomaly_entry = entry+'_cluster='+str(cluster_num)
        anomaly_entries.append(anomaly_entry)
           
    training_data = training_data.drop(entry,1)
    test_data = test_data.drop(entry,1)
       
'save intermediate result'     
training_data.to_csv("../data/swat_after_distribution_normal.csv", index=False)
test_data.to_csv("../data/swat_after_distribution_attack.csv", index=False)
# training_data = pd.read_csv("../../data/swat_after_distribution_normal.csv")
# test_data = pd.read_csv("../../data/swat_after_distribution_attack.csv")
      
'derive event driven predicates'
cont_vars = []
disc_vars = []
       
max_dict = {}
min_dict = {}
       
onehot_entries = {}
dead_entries = []
for entry in training_data:
    if entry.endswith('cluster') == True:
        newdf = pd.get_dummies(training_data[entry]).rename(columns=lambda x: entry + '=' + str(x))
        if len( newdf.columns.values.tolist() ) <= 1:
            unique_value = training_data[entry].unique()[0]
            dead_entries.append(entry + '=' + str(unique_value))
            training_data = pd.concat([training_data, newdf], axis=1)
            training_data = training_data.drop(entry, 1)
            testdf = pd.get_dummies(test_data[entry]).rename(columns=lambda x: entry + '=' + str(x))
            test_data = pd.concat([test_data, testdf], axis=1)
            test_data = test_data.drop(entry, 1)
        else:
            onehot_entries[entry]= newdf.columns.values.tolist()
            training_data = pd.concat([training_data, newdf], axis=1)
            training_data = training_data.drop(entry, 1)
            testdf = pd.get_dummies(test_data[entry]).rename(columns=lambda x: entry + '=' + str(x))
            test_data = pd.concat([test_data, testdf], axis=1)
            test_data = test_data.drop(entry, 1)
    else:
        if training_data[entry].dtypes == np.float64:
            max_value = training_data[entry].max()
            min_value = training_data[entry].min()
            if max_value == min_value:
                training_data = training_data.drop(entry, 1)
                test_data = test_data.drop(entry, 1)
            else:
                training_data[entry]=training_data[entry].apply(lambda x:float(x-min_value)/float(max_value-min_value))
                cont_vars.append(entry)
                max_dict[entry] = max_value
                min_dict[entry] = min_value
                test_data[entry]=test_data[entry].apply(lambda x:float(x-min_value)/float(max_value-min_value))
        else:
            newdf = pd.get_dummies(training_data[entry]).rename(columns=lambda x: entry + '=' + str(x))
            if len( newdf.columns.values.tolist() ) <= 1:
                unique_value = training_data[entry].unique()[0]
                dead_entries.append(entry + '=' + str(unique_value))
                training_data = pd.concat([training_data, newdf], axis=1)
                training_data = training_data.drop(entry, 1)
                
                for test_value in test_data[entry].unique():
                    if test_value != unique_value and len(test_data.loc[test_data[entry] == test_value,:])/len(test_data) < eps:
                        anomaly_entries.append(entry + '=' + str(test_value))
                       
                testdf = pd.get_dummies(test_data[entry]).rename(columns=lambda x: entry + '=' + str(x))
                test_data = pd.concat([test_data, testdf], axis=1)
                test_data = test_data.drop(entry, 1)
                       
            elif len( newdf.columns.values.tolist() ) == 2:
                disc_vars.append(entry)
                training_data[entry + '_shift'] = training_data[entry].shift(-1).fillna(method='ffill').astype(int).astype(str) + '->' + training_data[entry].astype(int).astype(str)
                onehot_entries[entry]= newdf.columns.values.tolist()
                training_data = pd.concat([training_data, newdf], axis=1)
                training_data = training_data.drop(entry, 1)
                       
                testdf = pd.get_dummies(test_data[entry]).rename(columns=lambda x: entry + '=' + str(x))
                test_data = pd.concat([test_data, testdf], axis=1)
                test_data = test_data.drop(entry, 1)
                   
            else:
                disc_vars.append(entry)
                training_data[entry + '_shift'] = training_data[entry].shift(-1).fillna(method='ffill').astype(int).astype(str) + '->' + training_data[entry].astype(int).astype(str)
                       
                training_data[entry + '!=1'] = 1
                training_data.loc[training_data[entry] == 1, entry + '!=1'] = 0
                       
                training_data[entry + '!=2'] = 1
                training_data.loc[training_data[entry] == 2, entry + '!=2'] = 0
                training_data = training_data.drop(entry, 1)
                       
                test_data[entry + '!=1'] = 1
                test_data.loc[test_data[entry] == 1, entry + '!=1'] = 0
                       
                test_data[entry + '!=2'] = 1
                test_data.loc[test_data[entry] == 2, entry + '!=2'] = 0
                test_data = test_data.drop(entry, 1)    
   
invar_dict = {}
for entry in disc_vars:  
    print('generate event-driven predicates for',entry)
    for roundi in [0, 1]:
        print( 'round: ' + str(roundi) )
        tempt_data = training_data.copy()
        tempt_data[entry] = 0
        if roundi == 0:
            tempt_data.loc[(tempt_data[entry+'_shift']=='1->0') | (tempt_data[entry+'_shift']=='1->2') | (tempt_data[entry+'_shift']=='0->2'), entry] = 99
        if roundi == 1:
            tempt_data.loc[(tempt_data[entry+'_shift']=='2->0') | (tempt_data[entry+'_shift']=='2->1') | (tempt_data[entry+'_shift']=='0->1'), entry] = 99
              
        for target_var in cont_vars:    
            active_vars = list(cont_vars)
            active_vars.remove(target_var)
                  
            X = tempt_data.loc[tempt_data[entry]==99, active_vars].values
            Y = tempt_data.loc[tempt_data[entry]==99, target_var].values
                  
            X_test = tempt_data[active_vars].values.astype(np.float)
            Y_test = tempt_data[target_var].values.astype(np.float)
                
            if len(Y)>5:
                lgRegr = Lasso(alpha=1, normalize=False)
                      
                lgRegr.fit(X, Y)
                y_pred = lgRegr.predict(X)
                    
                mae = metrics.mean_absolute_error(Y, y_pred)
                dist = list(np.array(Y) - np.array(y_pred))
                dist = map(abs, dist)
                max_error = max(dist)
                mae_test = metrics.mean_absolute_error(Y_test, lgRegr.predict( X_test ))
                      
                min_value = tempt_data.loc[tempt_data[entry]==99, target_var].min()
                max_value = tempt_data.loc[tempt_data[entry]==99, target_var].max()
#                 print(target_var,max_error)  
                if max_error < eps:
                    max_error = max_error*sigma
                    must = False
                    for coef in lgRegr.coef_:
                        if coef > 0:
                            must = True
                    if must == True:
                        invar_entry = Util.conInvarEntry(target_var, lgRegr.intercept_-max_error, '<', max_dict, min_dict, lgRegr.coef_, active_vars)
                        training_data[invar_entry] = 0
                        training_data.loc[training_data[target_var]< lgRegr.intercept_-max_error, invar_entry ] = 1
                              
                        invar_entry = Util.conInvarEntry(target_var, lgRegr.intercept_+max_error, '>', max_dict, min_dict, lgRegr.coef_, active_vars)
                        training_data[invar_entry] = 0
                        training_data.loc[training_data[target_var] > lgRegr.intercept_+max_error, invar_entry ] = 1
                    else:
                        if target_var not in invar_dict:
                            invar_dict[target_var] = []
                        icpList = invar_dict[target_var]
                            
                        if lgRegr.intercept_-max_error > 0  and lgRegr.intercept_-max_error <1:
                            invar_dict[target_var].append(lgRegr.intercept_-max_error)
                              
                        if lgRegr.intercept_+max_error > 0 and lgRegr.intercept_+max_error <1:
                            invar_dict[target_var].append(lgRegr.intercept_+max_error)
    training_data = training_data.drop(entry+'_shift',1)
          
for target_var in invar_dict:
    icpList = invar_dict[target_var]
    if icpList is not None and len(icpList) > 0:
        icpList.sort()
        if icpList is not None:
            for i in range(len(icpList)+1):
                if i == 0:
                    invar_entry = Util.conMarginEntry(target_var, icpList[0], 0, max_dict, min_dict)
                    training_data[invar_entry] = 0
                    training_data.loc[ training_data[target_var]<icpList[0], invar_entry ] = 1
                          
                    test_data[invar_entry] = 0
                    test_data.loc[ test_data[target_var]<icpList[0], invar_entry ] = 1
                          
                elif i == len(icpList):
                    invar_entry = Util.conMarginEntry(target_var, icpList[i-1], 1,  max_dict, min_dict)
                    training_data[invar_entry] = 0
                    training_data.loc[ training_data[target_var]>=icpList[i-1], invar_entry ] = 1
                          
                    test_data[invar_entry] = 0
                    test_data.loc[ test_data[target_var]>=icpList[i-1], invar_entry ] = 1
                          
                else:
                    invar_entry = Util.conRangeEntry(target_var, icpList[i-1],icpList[i], max_dict, min_dict)
                    training_data[invar_entry] = 0
                    training_data.loc[ (training_data[target_var]>=icpList[i-1]) & (training_data[target_var]<=icpList[i]), invar_entry ] = 1
                          
                    test_data[invar_entry] = 0
                    test_data.loc[ (test_data[target_var]>=icpList[i-1]) & (test_data[target_var]<=icpList[i]), invar_entry ] = 1
                     
for var_c in cont_vars:
    training_data = training_data.drop(var_c,1)
    test_data = test_data.drop(var_c,1) 
      
'save intermediate result'
training_data.to_csv("../data/after_event_normal.csv", index=False)
test_data.to_csv("../data/after_event_attack.csv", index=False)
# training_data = pd.read_csv("../data/after_event_normal.csv")
# test_data = pd.read_csv("../data/after_event_attack.csv")

'Rule mining'
keyArray = [['FIT101','LIT101','MV101','P101','P102'], ['AIT201','AIT202','AIT203','FIT201','MV201','P201','P202','P203','P204','P205','P206'],
         ['DPIT301','FIT301','LIT301','MV301','MV302','MV303','MV304','P301','P302'], ['AIT401','AIT402','FIT401','LIT401','P401','P402','P403','P404','UV401'],
         ['AIT501','AIT502','AIT503','AIT504','FIT501','FIT502','FIT503','FIT504','P501','P502','PIT501','PIT502','PIT503'],['FIT601','P601','P602','P603']]

print('Start rule mining')
print('Gamma=' + str(gamma_value) + ', theta=' + str(theta_value))
start_time = time.time()
rule_list_0, item_dict_0 = Util.getRules(training_data, dead_entries, keyArray, mode=0, gamma=gamma_value, max_k=max_k, theta=theta_value)
print('finish mode 0')
##mode 2 is quite costly, use mode 1 if want to save time
rule_list_1, item_dict_1 = Util.getRules(training_data, dead_entries, keyArray, mode=2, gamma=gamma_value, max_k=max_k, theta=theta_value)
print('finish mode 1')
end_time = time.time()
time_cost = (end_time-start_time)*1.0/60
print('rule mining time cost: ' + str(time_cost))
 
rules = []
for rule in rule_list_1:
    valid = False
    for item in rule[0]:
        if 'cluster' in item_dict_1[item]:
            valid = True
            break
    if valid == False:
        for item in rule[1]:
            if 'cluster' in item_dict_1[item]:
                valid = True
                break
    if valid == True:
        rules.append(rule)
rule_list_1 = rules
print('rule count: ' +str(len(rule_list_0) + len(rule_list_1)))
 
' arrange rules according to phase '
phase_dict = {}
for i in range(1,len(keyArray)+1):
    phase_dict[i] = []
 
for rule in rule_list_0:
    strPrint = ''
    first = True
    for item in rule[0]:
        strPrint += item_dict_0[item] + ' and '
        if first == True:
            first = False
            for i in range(0,len(keyArray)):
                for key in keyArray[i]:
                    if key in item_dict_0[item]:
                        phase = i+1
                        break
                     
    strPrint = strPrint[0:len(strPrint)-4] 
    strPrint += '---> '
    for item in rule[1]:
        strPrint += item_dict_0[item] + ' and '
    strPrint = strPrint[0:len(strPrint)-4]
    phase_dict[phase].append(strPrint)
 
for rule in rule_list_1:
    strPrint = ''
    first = True
    for item in rule[0]:
        strPrint += item_dict_1[item] + ' and '
        if first == True:
            first = False
            for i in range(0,6):
                for key in keyArray[i]:
                    if key in item_dict_1[item]:
                        phase = i+1
                        break
                        
    strPrint = strPrint[0:len(strPrint)-4] 
    strPrint += '---> '
    for item in rule[1]:
        strPrint += item_dict_1[item] + ' and '
    strPrint = strPrint[0:len(strPrint)-4]
    phase_dict[phase].append(strPrint)
 
# print ' print rules'
invariance_file = "../data/invariants/invariants_gamma=" + str(gamma_value)+'&theta=' + str(theta_value) + ".txt"
with open(invariance_file, "w") as myfile:
    for i in range(1,len(keyArray)+1):
        myfile.write('P' + str(i) + ':' + '\n')
        
         
        for rule in phase_dict[i]:
            myfile.write(rule + '\n')
            myfile.write('\n')
         
        myfile.write('--------------------------------------------------------------------------- '+'\n') 
    myfile.close()
       


###### use the invariants to do anomaly detection
# print 'start classification'
test_data['result'] = 0
for entry in anomaly_entries:
    test_data.loc[test_data[entry]==1,  'result'] = 1

test_data['actual_ret'] = 0
test_data.loc[test_data['Normal/Attack']!='Normal', 'actual_ret'] = 1
actual_ret = list(test_data['actual_ret'].values)

start_time = time.time()
num = 0
for rule in rule_list_0:
    num += 1
    test_data.loc[:,'antecedent'] = 1
    test_data.loc[:,'consequent'] = 1
    strPrint = ' '
    for item in rule[0]:
        if item_dict_0[item] in test_data:
            test_data.loc[test_data[ item_dict_0[item] ]==0,  'antecedent'] = 0
        else:
            test_data.loc[:,  'antecedent'] = 0
        strPrint += str(item_dict_0[item]) + ' '
    strPrint += '-->'
    for item in rule[1]:
        if item_dict_0[item] in test_data:
            test_data.loc[test_data[ item_dict_0[item] ]==0,  'consequent'] = 0
        else:
            test_data.loc[:,  'consequent'] = 0
        strPrint += ' ' + str(item_dict_0[item])
    test_data.loc[(test_data[ 'antecedent' ]==1) & (test_data[ 'consequent' ]==0),  'result'] = 1
    

for rule in rule_list_1:
    num += 1
    test_data.loc[:,'antecedent'] = 1
    test_data.loc[:,'consequent'] = 1
    strPrint = ' '
    for item in rule[0]:
        if item_dict_1[item] in test_data:
            test_data.loc[test_data[ item_dict_1[item] ]==0,  'antecedent'] = 0
        else:
            test_data.loc[:,  'antecedent'] = 0
        strPrint += str(item_dict_1[item]) + ' '
   
    strPrint += '-->'
       
    for item in rule[1]:
        if item_dict_1[item] in test_data:
            test_data.loc[test_data[ item_dict_1[item] ]==0,  'consequent'] = 0
        else:
            test_data.loc[:,  'antecedent'] = 1
        strPrint += ' ' + str(item_dict_1[item]) 
    test_data.loc[(test_data[ 'antecedent' ]==1) & (test_data[ 'consequent' ]==0),  'result'] = 1
       
end_time = time.time()
time_cost = (end_time-start_time)*1.0/60
print( 'detection time cost: ' + str(time_cost))
predict_ret = list(test_data['result'].values)

Util.evaluate_prediction(actual_ret,predict_ret, verbose=1)


 
