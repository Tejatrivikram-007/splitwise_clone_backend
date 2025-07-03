import React, { useState } from 'react';
import styles from '../style/GroupForm.module.css';

function GroupForm({ onGroupCreated }) {
  const [groupName, setGroupName] = useState('');
  const [members, setMembers] = useState(['', '']); // Start with 2 empty members
  const [adminIndex, setAdminIndex] = useState(0);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    // Filter out empty member names
    const validMembers = members.filter(name => name.trim() !== '');
    
    if (!groupName.trim()) {
      setError('Group name is required');
      setIsSubmitting(false);
      return;
    }

    if (validMembers.length < 2) {
      setError('Group must have at least 2 members');
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/groups/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: groupName,
          members: validMembers,
          admin_index: adminIndex,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Backend error:', errorData);
        throw new Error(errorData.detail || 'Failed to create group');
      }

      const newGroup = await response.json();
      onGroupCreated(newGroup);
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Fetch error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setGroupName('');
    setMembers(['', '']);
    setAdminIndex(0);
  };

  const handleMemberChange = (index, value) => {
    const updatedMembers = [...members];
    updatedMembers[index] = value;
    setMembers(updatedMembers);
  };

  const addMemberField = () => {
    setMembers([...members, '']);
  };

  const removeMemberField = (index) => {
    if (members.length > 2) { // Keep at least 2 members
      const updatedMembers = [...members];
      updatedMembers.splice(index, 1);
      setMembers(updatedMembers);
      
      // Adjust admin index if needed
      if (adminIndex >= updatedMembers.length) {
        setAdminIndex(updatedMembers.length - 1);
      } else if (adminIndex > index) {
        setAdminIndex(adminIndex - 1);
      }
    }
  };

  return (
    <div className={styles.groupFormContainer}>
      <h2 className={styles.groupFormTitle}>Create Group</h2>
      {error && <div className={styles.errorMessage}>{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className={styles.label}>Group Name</label>
          <input
            type="text"
            className={styles.inputField}
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            required
          />
        </div>

        <div className="mb-4">
          <label className={styles.label}>Group Members</label>
          {members.map((member, index) => (
            <div key={index} className={styles.memberRow}>
              <input
                type="text"
                placeholder="Member name"
                className={styles.inputField}
                value={member}
                onChange={(e) => handleMemberChange(index, e.target.value)}
                required
              />
              {members.length > 2 && (
                <button
                  type="button"
                  className={styles.removeButton}
                  onClick={() => removeMemberField(index)}
                  disabled={isSubmitting}
                >
                  Remove
                </button>
              )}
              <div className={styles.adminRadio}>
                <input
                  type="radio"
                  id={`admin-${index}`}
                  name="admin"
                  checked={adminIndex === index}
                  onChange={() => setAdminIndex(index)}
                  disabled={member.trim() === '' || isSubmitting}
                />
                <label htmlFor={`admin-${index}`}>Admin</label>
              </div>
            </div>
          ))}
          <button
            type="button"
            className={styles.addButton}
            onClick={addMemberField}
            disabled={isSubmitting}
          >
            + Add Another Member
          </button>
        </div>

        <button
          type="submit"
          className={styles.submitButton}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Creating...' : 'Create Group'}
        </button>
      </form>
    </div>
  );
}

export default GroupForm;