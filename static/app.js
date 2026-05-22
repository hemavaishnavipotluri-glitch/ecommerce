function addToCart(name, price, image) {

    fetch("/add-to-cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name,
            price,
            image
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
    });

}

    localStorage.setItem(

        "cart",
        JSON.stringify(cart)

    );

    alert("Product Added To Cart");
}