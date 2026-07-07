import React, { useState } from 'react';

/**
 * Policy Form Component
 * 
 * Form for creating new policies.
 */
interface PolicyFormProps {
  onSubmit: (policyData: any) => void;
}

export default function PolicyForm({ onSubmit }: PolicyFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('ECONOMIC');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, description, category });
    setName('');
    setDescription('');
    setCategory('ECONOMIC');
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <label htmlFor="name" style={{ display: 'block', marginBottom: '0.5rem' }}>
          Policy Name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #eaeaea',
            borderRadius: '4px'
          }}
        />
      </div>
      
      <div>
        <label htmlFor="description" style={{ display: 'block', marginBottom: '0.5rem' }}>
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={3}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #eaeaea',
            borderRadius: '4px',
            resize: 'vertical'
          }}
        />
      </div>
      
      <div>
        <label htmlFor="category" style={{ display: 'block', marginBottom: '0.5rem' }}>
          Category
        </label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #eaeaea',
            borderRadius: '4px'
          }}
        >
          <option value="ECONOMIC">Economic</option>
          <option value="SOCIAL">Social</option>
          <option value="CRIMINAL">Criminal</option>
          <option value="HEALTH">Health</option>
          <option value="EDUCATION">Education</option>
        </select>
      </div>
      
      <button
        type="submit"
        style={{
          padding: '0.75rem',
          backgroundColor: '#0070f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '1rem'
        }}
      >
        Create Policy
      </button>
    </form>
  );
}
