import React, { useState, useEffect } from 'react';
import styles from '../style/GroupBalance.module.css';

function GroupBalance({ groupId }) {
  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError('');

        const [groupRes, expensesRes] = await Promise.all([
          fetch(`http://localhost:8000/groups/${groupId}`),
          fetch(`http://localhost:8000/groups/${groupId}/expenses`)
        ]);

        if (!groupRes.ok) throw new Error('Failed to fetch group');
        if (!expensesRes.ok) throw new Error('Failed to fetch expenses');

        const [groupData, expensesData] = await Promise.all([
          groupRes.json(),
          expensesRes.json()
        ]);

        setGroup(groupData);
        setExpenses(expensesData);
      } catch (err) {
        setError(err.message);
        console.error('Fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    if (groupId) {
      fetchData();
    }
  }, [groupId]);

  const calculateBalances = () => {
    if (!group || !expenses) return { memberBalances: {}, totalGroupBalance: 0 };

    const memberBalances = {};
    const totalGroupBalance = expenses.reduce((sum, expense) => sum + expense.amount, 0);

    // Initialize balances for each member
    group.members.forEach(member => {
      memberBalances[member.id] = {
        name: member.name,
        paid: 0,
        owes: 0, // Total amount this member owes to others
        owed: 0, // Total amount owed to this member
        netBalance: 0,
        owesTo: {} // Detailed owes to specific members
      };
    });

    // Process each expense
    expenses.forEach(expense => {
      const payerId = expense.paid_by?.id;
      if (!payerId) return;

      // Add to payer's total paid amount
      memberBalances[payerId].paid += expense.amount;

      // Calculate each member's share
      let shares = {};
      if (expense.split_type === 'EQUAL') {
        const shareAmount = expense.amount / group.members.length;
        group.members.forEach(member => {
          if (member.id !== payerId) {
            shares[member.id] = shareAmount;
          }
        });
      } else if (expense.split_type === 'PERCENTAGE') {
        expense.splits.forEach(split => {
          if (split.user_id !== payerId && split.percentage) {
            shares[split.user_id] = (expense.amount * split.percentage) / 100;
          }
        });
      } else { // EXACT split
        expense.splits.forEach(split => {
          if (split.user_id !== payerId && split.amount) {
            shares[split.user_id] = split.amount;
          }
        });
      }

      // Update owes/owed relationships
      Object.entries(shares).forEach(([memberId, amount]) => {
        const debtorId = parseInt(memberId);
        
        // Update debtor's total owes
        memberBalances[debtorId].owes += amount;
        
        // Update payer's total owed
        memberBalances[payerId].owed += amount;
        
        // Track detailed owes
        memberBalances[debtorId].owesTo[payerId] = 
          (memberBalances[debtorId].owesTo[payerId] || 0) + amount;
      });
    });

    // Calculate net balances
    group.members.forEach(member => {
      const balance = memberBalances[member.id];
      balance.netBalance = balance.owed - balance.owes;
    });

    return { memberBalances, totalGroupBalance };
  };

  const renderOwesTable = (memberBalances) => {
    if (!group || !memberBalances) return null;

    const hasDebts = group.members.some(member => 
      Object.keys(memberBalances[member.id].owesTo).length > 0
    );

    if (!hasDebts) return null;

    return (
      <div className={styles.tableWrapper}>
        <table className={styles.detailedBalanceTable}>
          <thead>
            <tr>
              <th>Member</th>
              <th>Owes To</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {group.members.map(member => {
              const owesTo = memberBalances[member.id].owesTo;
              return Object.entries(owesTo).map(([toMemberId, amount]) => {
                const toMember = group.members.find(m => m.id === parseInt(toMemberId));
                return (
                  <tr key={`${member.id}-${toMemberId}`}>
                    <td>{member.name}</td>
                    <td>{toMember?.name || 'Unknown'}</td>
                    <td>₹{amount.toFixed(2)}</td>
                  </tr>
                );
              });
            })}
          </tbody>
        </table>
      </div>
    );
  };

  if (loading) return (
    <div className={styles.loadingContainer}>
      <div className={styles.spinner}></div>
      <p>Loading group data...</p>
    </div>
  );

  if (error) return (
    <div className={styles.errorContainer}>
      <h3>Error Loading Group</h3>
      <p>{error}</p>
      <button onClick={() => window.location.reload()}>Retry</button>
    </div>
  );

  if (!group) return (
    <div className={styles.notFound}>
      <h3>Group Not Found</h3>
      <p>The requested group could not be loaded.</p>
    </div>
  );

  const { memberBalances, totalGroupBalance } = calculateBalances();

  return (
    <div className={styles.groupBalanceContainer}>
      <header className={styles.header}>
        <h2>{group.name} - Balance Summary</h2>
        <p className={styles.totalBalance}>
          Total Group Expenses: ₹{totalGroupBalance.toFixed(2)}
        </p>
      </header>

      <section className={styles.section}>
        <h3>Detailed Owes</h3>
        {renderOwesTable(memberBalances) || 
          <p className={styles.noBalances}>No debts between members</p>}
      </section>

      <section className={styles.section}>
        <h3>Member Balances</h3>
        <div className={styles.tableWrapper}>
          <table className={styles.balanceTable}>
            <thead>
              <tr>
                <th>Member</th>
                <th>Paid</th>
                <th>Owes</th>
                <th>Owed</th>
                <th>Net Balance</th>
              </tr>
            </thead>
            <tbody>
              {group.members.map(member => {
                const balance = memberBalances[member.id];
                return (
                  <tr key={member.id}>
                    <td>{member.name}</td>
                    <td>₹{balance.paid.toFixed(2)}</td>
                    <td>₹{balance.owes.toFixed(2)}</td>
                    <td>₹{balance.owed.toFixed(2)}</td>
                    <td className={
                      balance.netBalance > 0.01 ? styles.positiveBalance :
                      balance.netBalance < -0.01 ? styles.negativeBalance : styles.zeroBalance
                    }>
                      ₹{Math.abs(balance.netBalance).toFixed(2)}
                      <span className={styles.balanceLabel}>
                        {balance.netBalance > 0.01 ? ' (gets back)' : 
                         balance.netBalance < -0.01 ? ' (owes)' : ' (settled)'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default GroupBalance;