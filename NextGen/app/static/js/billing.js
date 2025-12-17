// =====================================================
// FIXED BILLING.JS — CORRECT BLUEPRINT ROUTES
// =====================================================

let products = window.__INITIAL_PRODUCTS || [];
let cart = {};

const searchBox = document.getElementById("searchBox");
const resultBox = document.getElementById("resultBox");
const billBody = document.getElementById("billBody");
const netTxt = document.getElementById("net");
const checkoutBtn = document.getElementById("checkoutBtn");

// Base route for all calls
const BASE = "/dashboard/products/billing";

// =====================================================
// SEARCH
// =====================================================
searchBox.addEventListener("input", () => {
    let q = searchBox.value.trim().toLowerCase();
    if (!q) return (resultBox.innerHTML = "");

    fetch(`${BASE}/search?q=${q}`)
        .then(r => r.json())
        .then(showSearchResults);
});

function showSearchResults(list) {
    resultBox.innerHTML = "";

    if (!list.length) {
        resultBox.innerHTML = "<div style='color:white;padding:10px;'>No product found</div>";
        return;
    }

    list.forEach(p => {
        let div = document.createElement("div");
        div.style = `
            padding:10px;
            background:#ffffff22;
            color:white;
            margin-bottom:6px;
            border-radius:6px;
            cursor:pointer;
        `;
        div.innerHTML = `<b>${p.name}</b> <span style="float:right;">₹${p.selling_price}</span>`;
        div.onclick = () => addToCart(p);
        resultBox.appendChild(div);
    });
}

// =====================================================
// ADD TO CART
// =====================================================
function addToCart(p) {
    if (!cart[p.id]) {
        cart[p.id] = {
            id: p.id,
            name: p.name,
            price: parseFloat(p.selling_price),
            qty: 1
        };
    } else {
        cart[p.id].qty++;
    }
    renderCart();
}

// =====================================================
// RENDER CART
// =====================================================
function renderCart() {
    billBody.innerHTML = "";
    let total = 0;

    for (let id in cart) {
        let item = cart[id];
        let lineTotal = item.qty * item.price;
        total += lineTotal;

        let row = document.createElement("tr");
        row.innerHTML = `
            <td>
                <b>${item.name}</b><br>
                <small style="opacity:0.7;">ID: ${item.id}</small>
            </td>
            <td>
                <input type="number" min="1" value="${item.qty}" 
                    data-id="${id}" class="qtyBox" style="width:60px;">
            </td>
            <td>₹${item.price}</td>
            <td>₹${lineTotal}</td>
            <td>
                <button class="removeBtn" data-id="${id}"
                    style="background:#ff4d4d;border:none;color:white;
                    padding:3px 7px;border-radius:4px;cursor:pointer;">×</button>
            </td>
        `;
        billBody.appendChild(row);
    }

    netTxt.textContent = total;

    document.querySelectorAll(".qtyBox").forEach(inp => {
        inp.addEventListener("change", () => {
            let id = inp.dataset.id;
            cart[id].qty = parseInt(inp.value) || 1;
            renderCart();
        });
    });

    document.querySelectorAll(".removeBtn").forEach(btn => {
        btn.addEventListener("click", () => {
            delete cart[btn.dataset.id];
            renderCart();
        });
    });
}

// =====================================================
// CHECKOUT
// =====================================================
checkoutBtn.addEventListener("click", () => {
    let items = Object.values(cart).map(it => ({
        product_id: it.id,
        qty: it.qty,
        unit_price: it.price
    }));

    if (!items.length) return alert("Add items first!");

    fetch(`${BASE}/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items })
    })
        .then(r => r.json())
        .then(res => {
            if (res.message === "success") {
                alert("Bill saved successfully!");
                cart = {};
                renderCart();
                loadHistory();
            } else {
                alert("Error: " + res.error);
            }
        })
        .catch(err => console.error(err));
});

// =====================================================
// BILL HISTORY
// =====================================================
function renderHistoryList(bills) {
    const wrap = document.getElementById('billHistory');
    if (!wrap) return;

    if (!bills.length) {
        wrap.innerHTML = '<div style="color:#cfe3ff;padding:10px;">No bills yet.</div>';
        return;
    }

    let html = `
        <table style="width:100%;color:white;border-collapse:collapse;">
        <thead>
            <tr>
                <th>Bill No</th>
                <th>Date</th>
                <th>Items</th>
                <th>Amount</th>
                <th>Actions</th>
            </tr>
        </thead><tbody>
    `;

    bills.forEach(b => {
        const date = b.created_at ? new Date(b.created_at).toLocaleString() : "";

        html += `
            <tr>
                <td>${b.bill_no}</td>
                <td>${date}</td>
                <td>${b.item_count}</td>
                <td>₹${Number(b.net_amount).toFixed(2)}</td>
                <td>
                    <a href="${BASE}/print/${b.bill_no}" 
                        target="_blank" style="color:#84dfff;">Print</a>

                    <a href="${BASE}/pdf/${b.bill_no}"
                        style="color:#ffd580;margin-left:10px;">PDF</a>
                </td>
            </tr>
        `;
    });

    html += "</tbody></table>";
    wrap.innerHTML = html;
}

function loadHistory() {
    fetch(`${BASE}/history`)
        .then(r => r.json())
        .then(renderHistoryList)
        .catch(err => console.error("History Error:", err));
}

document.addEventListener("DOMContentLoaded", loadHistory);
