# Enable PHP Zip Extension for Faster Composer Installs

The zip extension is currently disabled, which makes `composer install` very slow. Here's how to enable it:

## Steps:

1. **Open PHP configuration file:**
   - Navigate to: `C:\xampp\php\php.ini`
   - Open it in a text editor (as Administrator if needed)

2. **Find and uncomment the zip extension:**
   - Search for: `;extension=zip`
   - Remove the semicolon to make it: `extension=zip`
   - Save the file

3. **Verify it's enabled:**
   ```powershell
   php -m | findstr zip
   ```
   You should see `zip` in the output.

4. **Restart Composer (if still running):**
   - Cancel the current `composer install` (Ctrl+C)
   - Run `composer install` again - it will be much faster!

## Alternative: Continue Without Zip Extension

If you prefer not to modify PHP settings, you can:
- Let the current `composer install` continue (it will work, just takes longer)
- Or cancel and run: `composer install --prefer-source` (explicitly use source)

The installation will complete either way, but with zip enabled it's 5-10x faster!

