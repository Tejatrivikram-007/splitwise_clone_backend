import React, { useState, useEffect } from 'react';
import styles from '../style/ExpenseForm.module.css';

function ExpenseForm({ groups, onExpenseCreated }) {
  const [formData, setFormData] = useState({
    selectedGroupId: '',
    description: '',
    amount: '',
    paidBy: '',
    splitType: 'equal'
  });
  const [splits, setSplits] = useState([]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [groupMembers, setGroupMembers] = useState([]);

  // Update splits when group, amount or split type changes
  useEffect(() => {
    if (formData.selectedGroupId && formData.amount) {
      const group = groups.find(g => g.id === parseInt(formData.selectedGroupId));
      if (group) {
        setGroupMembers(group.members);
        updateSplits(group.members, formData.splitType, formData.amount);
      }
    }
  }, [formData.selectedGroupId, formData.splitType, formData.amount, groups]);

  const updateSplits = (members, type, amt) => {
    const parsedAmount = parseFloat(amt) || 0;
    let newSplits = [];

    if (type === 'equal') {
      const splitAmount = parsedAmount / members.length;
      newSplits = members.map(member => ({
        user_id: member.id,
        name: member.name,
        amount: splitAmount,
        percentage: null
      }));
    } else if (type === 'percentage') {
      const defaultPercentage = 100 / members.length;
      newSplits = members.map(member => ({
        user_id: member.id,
        name: member.name,
        amount: 0,
        percentage: defaultPercentage
      }));
    } else if (type === 'exact') {
      const defaultAmount = parsedAmount / members.length;
      newSplits = members.map(member => ({
        user_id: member.id,
        name: member.name,
        amount: defaultAmount,
        percentage: null
      }));
    }

    setSplits(newSplits);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSplitChange = (index, field, value) => {
    const updatedSplits = [...splits];
    const numValue = parseFloat(value) || 0;
    
    updatedSplits[index][field] = numValue;
    
    // If percentage changed, recalculate amount
    if (field === 'percentage' && formData.splitType === 'percentage') {
      updatedSplits[index].amount = (parseFloat(formData.amount) * numValue) / 100;
    }
    
    setSplits(updatedSplits);
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setIsSubmitting(true);

  try {
    // Validate required fields
    if (!formData.selectedGroupId || !formData.description || !formData.amount || !formData.paidBy) {
      throw new Error('All fields are required');
    }

    // Convert amount to number
    const amount = parseFloat(formData.amount);
    if (amount <= 0 || isNaN(amount)) {
      throw new Error('Amount must be a positive number');
    }

    // Prepare the payload with correct structure
    const payload = {
      description: formData.description,
      amount: amount,
      paid_by: parseInt(formData.paidBy),
      split_type: formData.splitType.toUpperCase(), // Ensure uppercase
      splits: splits.map(split => ({
        user_id: split.user_id,
        ...(formData.splitType === 'percentage' ? { 
          percentage: parseFloat(split.percentage) 
        } : { 
          amount: parseFloat(split.amount) 
        })
      }))
    };

    // Debug: Log the final payload
    console.log("Final payload being sent:", JSON.stringify(payload, null, 2));

    const response = await fetch(
      `http://localhost:8000/groups/${formData.selectedGroupId}/expenses`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Backend error details:", errorData);
      throw new Error(errorData.detail || 'Failed to create expense');
    }

    const createdExpense = await response.json();
    onExpenseCreated(createdExpense);
    
    // Reset form
    setFormData({
      selectedGroupId: '',
      description: '',
      amount: '',
      paidBy: '',
      splitType: 'equal'
    });
    setSplits([]);
  } catch (err) {
    setError(err.message);
    console.error("Error creating expense:", err);
  } finally {
    setIsSubmitting(false);
  }
};

  return (
    <div className={styles.expenseFormContainer}>
      <h2>Add Expense</h2>
      {error && <div className={styles.error}>{error}</div>}
      
      <form onSubmit={handleSubmit}>
        {/* Group Selection */}
        <div className={styles.formGroup}>
          <label>Group</label>
          <select
            name="selectedGroupId"
            value={formData.selectedGroupId}
            onChange={handleChange}
            required
            disabled={isSubmitting}
          >
            <option value="">Select a group</option>
            {groups.map(group => (
              <option key={group.id} value={group.id}>{group.name}</option>
            ))}
          </select>
        </div>

        {/* Expense Details */}
        <div className={styles.formGroup}>
          <label>Description</label>
          <input
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            disabled={isSubmitting}
          />
        </div>

        <div className={styles.formGroup}>
          <label>Amount</label>
          <input
            type="number"
            name="amount"
            step="0.01"
            min="0.01"
            value={formData.amount}
            onChange={handleChange}
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Paid By Selection */}
        {formData.selectedGroupId && (
          <div className={styles.formGroup}>
            <label>Paid By</label>
            <select
              name="paidBy"
              value={formData.paidBy}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            >
              <option value="">Select member</option>
              {groupMembers.map(member => (
                <option key={member.id} value={member.id}>{member.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Split Type */}
        <div className={styles.formGroup}>
          <label>Split Type</label>
          <select
            name="splitType"
            value={formData.splitType}
            onChange={handleChange}
            disabled={isSubmitting}
          >
            <option value="equal">Equal</option>
            <option value="percentage">Percentage</option>
            <option value="exact">Exact Amount</option>
          </select>
        </div>

        {/* Split Details */}
        {formData.selectedGroupId && splits.length > 0 && (
          <div className={styles.splitsContainer}>
            <h3>Split Details</h3>
            <table className={styles.splitTable}>
              <thead>
                <tr>
                  <th>Member</th>
                  <th>{formData.splitType === 'percentage' ? 'Percentage' : 'Amount'}</th>
                </tr>
              </thead>
              <tbody>
                {splits.map((split, index) => (
                  <tr key={split.user_id}>
                    <td>{split.name}</td>
                    <td>
                      {formData.splitType === 'equal' ? (
                        <span>{(parseFloat(formData.amount) / splits.length).toFixed(2)}</span>
                      ) : formData.splitType === 'percentage' ? (
                        <input
                          type="number"
                          step="1"
                          min="0"
                          max="100"
                          value={split.percentage || ''}
                          onChange={(e) => handleSplitChange(index, 'percentage', e.target.value)}
                          disabled={isSubmitting}
                          required
                        />
                      ) : (
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={split.amount || ''}
                          onChange={(e) => handleSplitChange(index, 'amount', e.target.value)}
                          disabled={isSubmitting}
                          required
                        />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <button 
          type="submit" 
          disabled={isSubmitting}
          className={styles.submitButton}
        >
          {isSubmitting ? 'Creating...' : 'Add Expense'}
        </button>
      </form>
    </div>
  );
}

export default ExpenseForm;