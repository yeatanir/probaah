#!/bin/bash
echo "🔐 Setting up SSH keys for Roar Collab"
echo "======================================"

SSH_DIR="$HOME/.ssh"
KEY_NAME="roar_collab_probaah"

# Create .ssh directory if it doesn't exist
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# Generate SSH key if it doesn't exist
if [ ! -f "$SSH_DIR/$KEY_NAME" ]; then
    echo "🔑 Generating new SSH key..."
    ssh-keygen -t ed25519 -f "$SSH_DIR/$KEY_NAME" -C "probaah-$(date +%Y%m%d)"
    echo "✅ SSH key generated"
else
    echo "✅ SSH key already exists"
fi

# Add to SSH config
SSH_CONFIG="$SSH_DIR/config"
if ! grep -q "Host roar-collab" "$SSH_CONFIG" 2>/dev/null; then
    echo ""
    echo "📝 Adding to SSH config..."
    cat >> "$SSH_CONFIG" << EOF

# Probaah - Penn State Roar Collab
Host roar-collab
    HostName submit.aci.ics.psu.edu
    User akp6421
    IdentityFile ~/.ssh/$KEY_NAME
    IdentitiesOnly yes
EOF
    echo "✅ SSH config updated"
fi

echo ""
echo "🚀 Next steps:"
echo "1. Copy your public key:"
echo "   cat $SSH_DIR/$KEY_NAME.pub"
echo ""
echo "2. Add it to Roar Collab:"
echo "   ssh akp6421@submit.aci.ics.psu.edu"
echo "   mkdir -p ~/.ssh"
echo "   echo 'PASTE_YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo ""
echo "3. Test connection:"
echo "   ssh roar-collab 'echo Connection successful!'"
echo ""
echo "4. Test with Probaah:"
echo "   probaah jobs status"
