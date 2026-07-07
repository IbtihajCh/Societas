import React, { useState } from 'react';

import { PolicyCategory, PolicyCreateRequestDTO } from '@/types/api';

/**
 * Policy Form Component
 *
 * Form for creating new policies.
 */
interface PolicyFormProps {
  onSubmit: (policyData: PolicyCreateRequestDTO) => void;
}

const CATEGORY_OPTIONS: { value: PolicyCategory; label: string }[] = [
  { value: PolicyCategory.ECONOMIC, label: 'Economic' },
  { value: PolicyCategory.SOCIAL, label: 'Social' },
  { value: PolicyCategory.ENVIRONMENTAL, label: 'Environmental' },
  { value: PolicyCategory.PUBLIC_ORDER, label: 'Public Order' },
  { value: PolicyCategory.EDUCATION, label: 'Education' },
  { value: PolicyCategory.HEALTHCARE, label: 'Healthcare' },
  { value: PolicyCategory.INFRASTRUCTURE, label: 'Infrastructure' },
  { value: PolicyCategory.CULTURAL, label: 'Cultural' },
];

export default function PolicyForm({ onSubmit }: PolicyFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<PolicyCategory>(
    PolicyCategory.ECONOMIC,
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, description, category });
    setName('');
    setDescription('');
    setCategory(PolicyCategory.ECONOMIC);
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
    >
      <div>
        <label
          htmlFor="name"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
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
            borderRadius: '4px',
          }}
        />
      </div>

      <div>
        <label
          htmlFor="description"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
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
            resize: 'vertical',
          }}
        />
      </div>

      <div>
        <label
          htmlFor="category"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
          Category
        </label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value as PolicyCategory)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #eaeaea',
            borderRadius: '4px',
          }}
        >
          {CATEGORY_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
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
          fontSize: '1rem',
        }}
      >
        Create Policy
      </button>
    </form>
  );
}
