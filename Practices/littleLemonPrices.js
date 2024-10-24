let foods = [["Italian pasta", "Ricec with veggies", "Chicken with potatoes","Vegetarian Pizza"], [9.55,8.65,15.55,6.45]]

function priceList(tax) {
    if (tax) {
        console.log("Prices with 20% tax:");
        for (let i = 0; i < foods[0].length; i++) {
            console.log(`Dish: ${foods[0][i]} Price(incl.tax): $${(foods[1][i]*1.2)}`); 
        }
    }
    else{
        console.log("Prices without tax:");
        for (let i = 0; i < foods[0].length; i++) {
            console.log(`Dish: ${foods[0][i]} Price: $${foods[1][i]}`); 
        }
    }
}

priceList(true);
console.log("");
priceList(false);