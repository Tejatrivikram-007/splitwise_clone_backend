import React, { useState, useEffect } from 'react';
import GroupForm from './components/GroupForm';
import ExpenseForm from './components/ExpenseForm';
import GroupBalance from './components/GroupBalance';
import styles from './style/App.module.css';

function App() {
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://backend:8000';

  useEffect(() => {
    // Fetch initial data
    fetch(`${backendUrl}/users/`)
      .then(res => res.json())
      .then(data => setUsers(data))
      .catch(err => console.error("Error fetching users:", err));

    fetch(`${backendUrl}/groups/`)
      .then(res => res.json())
      .then(data => setGroups(data))
      .catch(err => console.error("Error fetching groups:", err));
  }, []);

  const handleGroupCreated = (newGroup) => {
    setGroups([...groups, newGroup]);
  };

  const handleExpenseCreated = () => {
    // Refresh group expenses and balances
    if (selectedGroup) {
      fetch(`http://localhost:8000/groups/${selectedGroup}`)
        .then(res => res.json())
        .then(data => {
          setGroups(groups.map(g => g.id === data.id ? data : g));
        });
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>
        Splitwise Clone
      </h1>

      <div className={styles.grid}>
        <div className={styles.leftColumn}>
          <GroupForm users={users} onGroupCreated={handleGroupCreated} />
          <ExpenseForm 
            groups={groups} 
            users={users} 
            onExpenseCreated={handleExpenseCreated} 
          />
        </div>
        
        <div className={styles.rightColumn}>
          <div className={styles.groupBalanceContainer}>
            <h2>Group Balances</h2>
            <select 
              className={styles.select}
              onChange={(e) => setSelectedGroup(e.target.value)}
              value={selectedGroup || ''}
            >
              <option value="">Select a group</option>
              {groups.map(group => (
                <option key={group.id} value={group.id}>{group.name}</option>
              ))}
            </select>
            {selectedGroup && <GroupBalance groupId={selectedGroup} />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
