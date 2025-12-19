# Bakery Quotation Frontend

Modern Next.js frontend for the Bakery Quotation System. Built with React, TypeScript, Tailwind CSS, and shadcn/ui components.

## Features

- 🎨 Modern UI with Tailwind CSS and shadcn/ui
- 📱 Fully responsive design
- 🌙 Dark mode support
- ⚡ Fast and optimized with Next.js 15
- 🔄 Real-time quote generation
- ✅ Form validation and error handling

## Tech Stack

- **Framework:** Next.js 15.4.3
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4
- **UI Components:** Radix UI / shadcn/ui
- **Icons:** Lucide React
- **Package Manager:** npm

## Prerequisites

- Node.js 20+ or higher
- npm or yarn
- Bakery Quotation API running on http://localhost:8001

## Installation

```bash
# Install dependencies
npm install

# or with yarn
yarn install
```

## Configuration

Create a `.env.local` file:

```bash
# Bakery Quotation API Backend URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

## Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Main quotation page
│   │   └── api/                # API routes (if needed)
│   ├── components/
│   │   └── ui/                 # Reusable UI components
│   │       ├── sidebar.tsx
│   │       ├── chatgpt-prompt-input.tsx
│   │       ├── button.tsx
│   │       └── ...
│   └── lib/
│       ├── bakery-api.ts       # API integration layer
│       └── utils.ts            # Utility functions
├── public/                      # Static assets
├── .env.local                   # Environment variables
├── next.config.ts               # Next.js configuration
├── tailwind.config.ts           # Tailwind configuration
└── package.json
```

## API Integration

The frontend communicates with the FastAPI backend through the `/src/lib/bakery-api.ts` module:

### Available API Functions

```typescript
// Get available job types
const jobTypes = await getAvailableJobTypes();

// Create a quotation
const quote = await createQuotation({
  customer_name: "John Doe",
  job_type: "cupcakes",
  quantity: 24,
  due_date: "2025-12-25",
  company_name: "Artisan Bakery",
  notes: "Special order"
});

// Check API health
const health = await checkApiHealth();
```

## Usage

1. **Start the Backend API:**
   ```bash
   cd ../
   uvicorn src.app.main:app --reload --port 8001
   ```

2. **Start the Frontend:**
   ```bash
   npm run dev
   ```

3. **Create a Quotation:**
   - Open http://localhost:3000
   - Type a message to start
   - Fill in the quotation form
   - Submit to generate a quote

## Features in Detail

### Quotation Form

- **Customer Name:** Required field for customer identification
- **Job Type:** Dropdown populated from API (cupcakes, cake, pastry_box)
- **Quantity:** Number input with minimum value of 1
- **Due Date:** Date picker with minimum date as today
- **Company Name:** Optional, defaults to "Artisan Bakery"
- **Notes:** Optional textarea for additional information

### Quote Display

After successful generation, the quote details are displayed:
- Quote ID
- Total cost with currency
- Creation timestamp
- File path (for backend reference)

### Error Handling

- Form validation errors are displayed inline
- API errors are shown in error banners
- Connection issues are handled gracefully

## Customization

### Theming

The app uses Tailwind CSS with a custom color scheme. Primary color is `#23938c` (teal).

To change colors, edit `tailwind.config.ts`:

```typescript
theme: {
  extend: {
    colors: {
      primary: '#23938c',
      // Add more custom colors
    }
  }
}
```

### Components

All UI components are in `src/components/ui/` and can be customized individually.

## Production Deployment

```bash
# Build the application
npm run build

# Start production server
npm start
```

For deployment to Vercel, Netlify, or other platforms, follow their respective documentation.

## Troubleshooting

### Cannot connect to API

- Ensure the backend is running on port 8001
- Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
- Verify CORS is enabled in the FastAPI backend

### TypeScript errors

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Styling issues

```bash
# Rebuild Tailwind
npm run build
```

## License

MIT

## Related

- [Backend API](../README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
