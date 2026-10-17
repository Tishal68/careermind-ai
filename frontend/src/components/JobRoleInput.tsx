import React from 'react';

// Examples only: a profession never has to appear here to be accepted.
export const ROLE_SUGGESTIONS = ['Accountant', 'Architect', 'Civil Engineer', 'Electrician', 'Graphic Designer', 'Human Resources Manager', 'Lawyer', 'Marketing Manager', 'Mechanical Engineer', 'Nurse', 'Operations Manager', 'Pharmacist', 'Product Designer', 'Project Manager', 'Research Scientist', 'Sales Manager', 'School Teacher', 'Social Worker', 'Software Engineer', 'Supply Chain Analyst'];

export default function JobRoleInput({id, value, onChange}: {id: string; value: string; onChange: (value: string) => void}) {
  return <>
    <input id={id} list={`${id}-suggestions`} value={value} onChange={e => onChange(e.target.value)} required minLength={2} maxLength={100} aria-describedby={`${id}-hint`} placeholder="Enter any job title, including your own specialization" className="w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white" />
    <datalist id={`${id}-suggestions`}>{ROLE_SUGGESTIONS.map(role => <option key={role} value={role} />)}</datalist>
    <p id={`${id}-hint`} className="text-xs text-slate-400">Type any professional role. Suggestions are examples, not a restricted list.</p>
  </>;
}
