from sklearn.linear_model import LogisticRegression
clf2 = MultiOutputClassifier(LogisticRegression(max_iter=1000))
clf2.fit(Xtr, ytr)
y_prob = clf2.predict_proba(Xte)  # lista de 25 arrays
# P(número i sai) = y_prob[i][:,1]
probs = np.array([p[:,1] for p in y_prob]).T  # shape (n_amostras,25)
print("Prob média saída do nº 7:", probs[:,6].mean())
