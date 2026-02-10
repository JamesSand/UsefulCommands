

### Convex

Convex function

for all $x, x',\lambda \in [0, 1]$,

$$
f(\lambda x + (1 - \lambda) x') \leq \lambda f(x) + (1 - \lambda) f(x')
$$


Strict Convex

for all $x \neq x',\lambda \in (0, 1)$,
$$
f(\lambda x + (1 - \lambda) x') < \lambda f(x) + (1 - \lambda) f(x')
$$

Strongly Convex with parameter $\mu > 0$

for all $x, y$,
$$
f(y) \ge f(x) + \nabla f(x)^T (y - x) + \frac{\mu}{2} \| y - x \|^2
$$

从上边这个定义能够推导出下边这种等价的形式定义：直观上来理解，中间点的函数值要比线性插值更低一个二次项
$$
f((1 - \lambda) x + \lambda y) \le (1 - \lambda) f(x) + \lambda f(y) - \frac{\mu}{2} \lambda (1 - \lambda) \| y - x \|^2
$$


值得注意的是，strong convex 这里的结论和下边 L smooth 的结论是相反的。
- strongly convex 是 $f(y) - f(x) \ge xxx$ 是一个变化量的下届
- L smooth 是 $f(y) - f(x) \le xxx$ 是变化量的上届

### Smooth


L-smooth function

for all $x, x'$,
$$
\| \nabla f(x) - \nabla f(x') \| \leq L \| x - x' \|
$$

这个东西刻画的是函数的梯度变化速度，有下边等价的定义形式
$$
f(y) \le f(x) + \nabla f(x)^T (y - x) + \frac{L}{2} \| y - x \|^2
$$


















